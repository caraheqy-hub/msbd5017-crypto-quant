import { network } from "hardhat";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { anchorAudit, verifyAudit, fileHash, saveJson } from "./audit-tools.js";
try {
  // Explicit simulated connection: no HTTP or testnet connection is selected.
  const connection = await network.create("hardhatMainnet");
  const registry = await connection.ethers.deployContract("BacktestRegistry");
  await registry.waitForDeployment();
  const address = await registry.getAddress();
  const output = join("build", "local-demo", new Date().toISOString().replace(/[:.]/g, "-"));
  const results = [];
  for (const name of ["ma60", "ema20", "williams14"]) {
    const file = `final_project/cases/${name}/audit_package.json`;
    const before = fileHash(file);
    const proof = await anchorAudit(connection, file, join(output, `${name}.proof.json`), address);
    await verifyAudit(connection, file, proof);
    console.log(`${name}: ORIGINAL PASSED (record ${proof.record_id})`);
    const modified = JSON.parse(readFileSync(file, "utf8"));
    modified.trades[0].qty += 0.01;
    const copy = join(output, `${name}.tampered.json`);
    saveJson(copy, modified);
    let detected = false;
    try { await verifyAudit(connection, copy, proof); }
    catch (error) {
      if (!(error instanceof Error) || !error.message.includes("file fingerprint mismatch")) throw error;
      detected = true;
    }
    if (!detected) throw new Error("Tampered file unexpectedly passed");
    console.log(`${name}: TAMPER DETECTED`);
    await verifyAudit(connection, file, proof);
    if (fileHash(file) !== before) throw new Error("Original file changed");
    results.push({ case: name, original_passed: true, tamper_detected: true, original_unchanged: true, proof });
  }
  saveJson(join(output, "summary.json"), { network: "in-process simulated chain; ephemeral", results });
  console.log("LOCAL DEMO PASSED. Evidence:", output);
  console.log("This chain ends with the process. Proofs are local demonstration evidence only.");
} catch (error) { console.error(error); process.exitCode = 1; }
