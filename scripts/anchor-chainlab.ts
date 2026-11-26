import { network } from "hardhat";
import { existsSync,unlinkSync } from "node:fs";
import { anchorAuditWithPolicy,saveJson } from "./audit-tools.js";
import { manifest,preflight,requireChainlab } from "./chainlab-tools.js";
try {
 const connection=await network.create("chainlab");
 try {
  const {paths,hash,existingRecord}=await preflight(connection);
  if(existsSync(paths.proof)) throw new Error("Testnet proof exists; verify instead of resubmitting");
  if(existingRecord!==null) throw new Error(`Already anchored at record ${existingRecord}; recover its proof`);
  const [signer]=await connection.ethers.getSigners();
  if(!signer || (await signer.getAddress()).toLowerCase()!==manifest.expected_account.toLowerCase()) throw new Error("Configured signer differs from preflight account");
  console.log("Sending ONE chainlab anchoring transaction for",paths.name);
  const proof=await anchorAuditWithPolicy(connection,paths.file,paths.proof,manifest.contract_address,requireChainlab,
   tx=>saveJson(paths.pending,{network:"chainlab",case:paths.name,sha256:hash,transaction_hash:tx,contract_address:manifest.contract_address}));
  proof.file=`final_project/cases/${paths.name}/audit_package.json`;
  saveJson(paths.proof,proof);unlinkSync(paths.pending);
  console.log("CHAINLAB ANCHOR SUCCESS",proof);console.log("Proof saved:",paths.proof);
 }finally{await connection.close();}
}catch(error){console.error(error);process.exitCode=1;}
