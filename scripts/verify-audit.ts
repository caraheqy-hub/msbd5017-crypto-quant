
import { network } from "hardhat";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const AUDIT_PACKAGE = "audit/audit_package.json";
const AUDIT_PROOF = "audit/audit_package.proof.json";

async function main() {
  const { ethers } = await network.create();

  const proof = JSON.parse(readFileSync(resolve(AUDIT_PROOF), "utf8"));

  const networkInfo = await ethers.provider.getNetwork();
  if (networkInfo.chainId.toString() !== proof.chain_id) {
    throw new Error("Wrong blockchain network");
  }

  const fileBytes = readFileSync(resolve(AUDIT_PACKAGE));
  const localHash = "0x" + createHash("sha256").update(fileBytes).digest("hex");

  const registry = await ethers.getContractAt("BacktestRegistry", proof.contract_address);
  const onChainHash: string = await registry.getHash(BigInt(proof.record_id));

  const matches = localHash.toLowerCase() === onChainHash.toLowerCase();

  console.log("\n===== AUDIT VERIFICATION =====");
  console.log("File:", AUDIT_PACKAGE);
  console.log("Local Hash:", localHash);
  console.log("On-chain Hash:", onChainHash);

  if (matches) {
    console.log("\nAUDIT VERIFICATION PASSED");
  } else {
    console.log("\nAUDIT VERIFICATION FAILED");
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
