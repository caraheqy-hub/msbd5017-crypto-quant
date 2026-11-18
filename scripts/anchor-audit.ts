
import { network } from "hardhat";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const CONTRACT_ADDRESS = "0x35887245652F53eA72c8D6a9FD595c9bE78Cb284";
const AUDIT_PACKAGE = "audit/audit_package.json";
const AUDIT_PROOF = "audit/audit_package.proof.json";

async function main() {
  const { ethers } = await network.create();

  if (!ethers.isAddress(CONTRACT_ADDRESS)) {
    throw new Error("Please set a valid contract address");
  }

  const networkInfo = await ethers.provider.getNetwork();
  console.log("Chain ID:", networkInfo.chainId.toString());

  // The audit package is the canonical JSON built by audit/build_audit_package.py.
  const fileBytes = readFileSync(resolve(AUDIT_PACKAGE));
  const hash = "0x" + createHash("sha256").update(fileBytes).digest("hex");
  console.log("Audit package SHA-256:", hash);

  const registry = await ethers.getContractAt("BacktestRegistry", CONTRACT_ADDRESS);

  console.log("Submitting transaction...");
  const tx = await registry.anchorBacktest(hash);
  console.log("Transaction Hash:", tx.hash);

  const receipt = await tx.wait();
  if (!receipt || receipt.status !== 1) {
    throw new Error("Transaction failed");
  }

  let recordId: string | undefined;
  for (const log of receipt.logs) {
    try {
      const parsed = registry.interface.parseLog(log);
      if (parsed?.name === "BacktestAnchored") {
        recordId = parsed.args.recordId.toString();
        break;
      }
    } catch {
      // 忽略不属于该合约事件的日志
    }
  }

  if (recordId === undefined) {
    throw new Error("BacktestAnchored event not found");
  }

  const proof = {
    contract_address: CONTRACT_ADDRESS,
    chain_id: networkInfo.chainId.toString(),
    record_id: recordId,
    transaction_hash: tx.hash,
    block_number: receipt.blockNumber,
    file: AUDIT_PACKAGE,
    sha256: hash,
  };

  writeFileSync(resolve(AUDIT_PROOF), JSON.stringify(proof, null, 2) + "\n", "utf8");

  console.log("\n===== AUDIT ANCHOR SUCCESS =====");
  console.log("Record ID:", recordId);
  console.log("Proof saved:", AUDIT_PROOF);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
