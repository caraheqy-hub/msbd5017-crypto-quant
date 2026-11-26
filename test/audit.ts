import assert from "node:assert/strict";
import { mkdtempSync, rmSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { network } from "hardhat";
import { anchorAudit, verifyAudit, saveJson, requireLocal } from "../scripts/audit-tools.js";

const connection = await network.create("hardhatMainnet");
describe("Audit integration (simulated chain)", function () {
  it("anchors a real package, rejects tampering and invalid proofs, preserves the original", async function () {
    const temp = mkdtempSync(join(tmpdir(), "audit-test-"));
    try {
      const registry = await connection.ethers.deployContract("BacktestRegistry");
      await registry.waitForDeployment();
      const file = "final_project/cases/ma60/audit_package.json";
      const original = readFileSync(file);
      const proofPath = join(temp, "proof.json");
      const proof = await anchorAudit(connection, file, proofPath, await registry.getAddress());
      await verifyAudit(connection, file, proof);
      const modified = JSON.parse(original.toString("utf8"));
      modified.trades[0].qty += 0.01;
      const tampered = join(temp, "tampered.json");
      saveJson(tampered, modified);
      await assert.rejects(verifyAudit(connection, tampered, proof), /fingerprint mismatch/);
      await assert.rejects(verifyAudit(connection, file, { ...proof, chain_id: "1" }), /Wrong blockchain network/);
      await assert.rejects(verifyAudit(connection, file, { ...proof, genesis_hash: "0x" + "00".repeat(32) }), /Wrong genesis/);
      await assert.rejects(verifyAudit(connection, file, { ...proof, transaction_hash: "0x" + "00".repeat(32) }), /Proof transaction/);
      await assert.rejects(anchorAudit(connection, file, proofPath, await registry.getAddress()), /already exists/);
      await verifyAudit(connection, file, proof);
      assert.deepEqual(readFileSync(file), original);
    } finally { rmSync(temp, { recursive: true, force: true }); }
  });
  it("accepts resolved localhost URLs and rejects remote URLs before RPC or signing", async function () {
    for (const address of ["http://127.0.0.1:8545", "http://localhost:8545", "http://[::1]:8545"]) {
      const local = { networkConfig: { type: "http", url: { getUrl: async () => address } } } as unknown as Parameters<typeof requireLocal>[0];
      await requireLocal(local);
    }
    for (const address of ["https://testnet.chainlab.fun", "http://127.0.0.1.example.com:8545"]) {
      const remote = { networkConfig: { type: "http", url: { getUrl: async () => address } } } as unknown as Parameters<typeof requireLocal>[0];
      await assert.rejects(requireLocal(remote), /Local networks only/);
    }
  });
});
