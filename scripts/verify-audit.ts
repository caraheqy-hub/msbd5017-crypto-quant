import { network } from "hardhat";
import { readFileSync } from "node:fs";
import { verifyAudit, packageFile, proofFile } from "./audit-tools.js";
try {
  await verifyAudit(await network.create(), packageFile(), JSON.parse(readFileSync(proofFile(), "utf8")));
  console.log("AUDIT VERIFICATION PASSED");
} catch (error) { console.error(error); process.exitCode = 1; }
