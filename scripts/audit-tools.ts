import { network } from "hardhat";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

type Connection = Awaited<ReturnType<typeof network.create>>;
export interface AuditProof {
  schema: "msbd5017.proof.v1";
  chain_id: string;
  genesis_hash: string;
  contract_address: string;
  record_id: string;
  transaction_hash: string;
  block_number: number;
  block_hash: string;
  submitter: string;
  file: string;
  sha256: string;
}
export const packageFile = () => process.env.AUDIT_PACKAGE ?? "final_project/cases/ma60/audit_package.json";
export const proofFile = () => process.env.AUDIT_PROOF ?? "build/proofs/ma60.local.proof.json";
export async function requireLocal(connection: Connection): Promise<void> {
  const config = connection.networkConfig;
  if (config.type === "edr-simulated") return;
  if (config.type === "http") {
    const url = new URL(await config.url.getUrl());
    if (url.protocol === "http:" && ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname)) return;
  }
  throw new Error("Local networks only: testnet transactions are disabled in these audit tools");
}
export function fileHash(file: string): string {
  return "0x" + createHash("sha256").update(readFileSync(resolve(file))).digest("hex");
}
export function saveJson(file: string, value: unknown): void {
  mkdirSync(dirname(resolve(file)), { recursive: true });
  writeFileSync(resolve(file), JSON.stringify(value, null, 2) + "\n", "utf8");
}
export async function anchorAuditWithPolicy(connection: Connection, file: string, proofPath: string, address: string, checkNetwork: typeof requireLocal, onSubmitted?: (hash: string) => void): Promise<AuditProof> {
  await checkNetwork(connection);
  const { ethers } = connection;
  if (existsSync(proofPath)) throw new Error("Proof already exists; choose a new AUDIT_PROOF path");
  // Check input and output location before sending a transaction.
  const hash = fileHash(file);
  JSON.parse(readFileSync(file, "utf8"));
  mkdirSync(dirname(resolve(proofPath)), { recursive: true });
  if (!ethers.isAddress(address) || await ethers.provider.getCode(address) === "0x") throw new Error("No registry contract at address");
  const registry = await ethers.getContractAt("BacktestRegistry", address);
  const tx = await registry.anchorBacktest(hash);
  console.log("Submitted transaction:", tx.hash);
  onSubmitted?.(tx.hash);
  const receipt = await tx.wait();
  if (!receipt || receipt.status !== 1) throw new Error("Transaction failed");
  const event = receipt.logs.filter(log => log.address.toLowerCase() === address.toLowerCase())
    .map(log => { try { return registry.interface.parseLog(log); } catch { return null; } })
    .find(log => log?.name === "BacktestAnchored" && log.args.dataHash.toLowerCase() === hash.toLowerCase());
  if (!event) throw new Error("BacktestAnchored event missing");
  const genesis = await ethers.provider.getBlock(0);
  if (!genesis?.hash) throw new Error("Genesis block unavailable");
  const proof: AuditProof = {
    schema: "msbd5017.proof.v1", chain_id: (await ethers.provider.getNetwork()).chainId.toString(),
    genesis_hash: genesis.hash, contract_address: address,
    record_id: event.args.recordId.toString(), transaction_hash: tx.hash,
    block_number: receipt.blockNumber, block_hash: receipt.blockHash,
    submitter: event.args.submitter, file, sha256: hash,
  };
  saveJson(proofPath, proof);
  return proof;
}
export async function verifyAuditWithPolicy(connection: Connection, file: string, proof: AuditProof, checkNetwork: typeof requireLocal): Promise<void> {
  await checkNetwork(connection);
  const { ethers } = connection;
  if (proof.schema !== "msbd5017.proof.v1" || !/^\d+$/.test(proof.record_id)) throw new Error("Invalid proof format");
  if ((await ethers.provider.getNetwork()).chainId.toString() !== proof.chain_id) throw new Error("Wrong blockchain network");
  const genesis = await ethers.provider.getBlock(0);
  if (genesis?.hash !== proof.genesis_hash) throw new Error("Wrong genesis block");
  if (!ethers.isAddress(proof.contract_address) || await ethers.provider.getCode(proof.contract_address) === "0x") throw new Error("Registry contract missing; local chain may have restarted");
  const registry = await ethers.getContractAt("BacktestRegistry", proof.contract_address);
  const localHash = fileHash(file);
  const onChainHash = await registry.getHash(BigInt(proof.record_id));
  if (localHash.toLowerCase() !== proof.sha256.toLowerCase() || localHash.toLowerCase() !== onChainHash.toLowerCase()) throw new Error("AUDIT VERIFICATION FAILED: file fingerprint mismatch");
  const receipt = await ethers.provider.getTransactionReceipt(proof.transaction_hash);
  if (!receipt || receipt.status !== 1 || receipt.blockNumber !== proof.block_number || receipt.blockHash !== proof.block_hash) throw new Error("Proof transaction does not match this chain");
  const event = receipt.logs.filter(log => log.address.toLowerCase() === proof.contract_address.toLowerCase())
    .map(log => { try { return registry.interface.parseLog(log); } catch { return null; } })
    .find(log => log?.name === "BacktestAnchored" && log.args.recordId.toString() === proof.record_id && log.args.dataHash.toLowerCase() === localHash.toLowerCase() && log.args.submitter.toLowerCase() === proof.submitter.toLowerCase());
  if (!event) throw new Error("Proof does not match anchoring event");
}

// Existing local entry points retain the original local-only policy.
export async function anchorAudit(connection: Connection, file: string, proofPath: string, address: string): Promise<AuditProof> {
  return anchorAuditWithPolicy(connection, file, proofPath, address, requireLocal);
}
export async function verifyAudit(connection: Connection, file: string, proof: AuditProof): Promise<void> {
  return verifyAuditWithPolicy(connection, file, proof, requireLocal);
}
