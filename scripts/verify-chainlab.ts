import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { verifyAuditWithPolicy } from "./audit-tools.js";
import type { AuditProof } from "./audit-tools.js";
import { manifest,requireChainlab,casePaths,readOnlyConnection } from "./chainlab-tools.js";
try {
 const paths=casePaths();const proof:AuditProof=JSON.parse(readFileSync(paths.proof,"utf8"));
 if(proof.contract_address.toLowerCase()!==manifest.contract_address.toLowerCase() || proof.chain_id!==manifest.chain_id || proof.genesis_hash!==manifest.genesis_hash) throw new Error("Proof is not for the expected chainlab registry");
 const connection=await readOnlyConnection();
 try {
  await verifyAuditWithPolicy(connection,process.env.AUDIT_VERIFY_FILE?resolve(process.env.AUDIT_VERIFY_FILE):paths.file,proof,requireChainlab);
  console.log("CHAINLAB VERIFICATION PASSED. Read-only; no transaction signed or sent.");
 }finally{await connection.close();}
}catch(error){console.error(error);process.exitCode=1;}
