import assert from "node:assert/strict";
import { mkdtempSync,rmSync,readFileSync,writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { network } from "hardhat";
import { requireChainlab,requirePackage,manifest,casePaths } from "../scripts/chainlab-tools.js";
import { anchorAuditWithPolicy,verifyAuditWithPolicy,requireLocal } from "../scripts/audit-tools.js";

type Connection=Parameters<typeof requireChainlab>[0];
function fake(options:{url?:string;chain?:bigint;genesis?:string;code?:string}={}):Connection {
 return {networkName:"chainlab",networkConfig:{type:"http",url:{getUrl:async()=>options.url??manifest.rpc_url}},
 ethers:{provider:{getNetwork:async()=>({chainId:options.chain??31337n}),getBlock:async()=>({hash:options.genesis??manifest.genesis_hash}),getCode:async()=>options.code??"0x1234"}}} as unknown as Connection;
}
describe("Explicit chainlab tools (no testnet transactions)",function(){
 it("pins endpoint, chain, genesis and contract presence",async function(){
  await requireChainlab(fake());
  await assert.rejects(requireChainlab(fake({url:"http://127.0.0.1:8545"})),/endpoint/);
  await assert.rejects(requireChainlab(fake({chain:1n})),/chain ID/);
  await assert.rejects(requireChainlab(fake({genesis:"0x00"})),/genesis/);
  await assert.rejects(requireChainlab(fake({code:"0x"})),/missing/);
 });
 it("rejects changed packages and keeps testnet proof paths separate",function(){
  const saved=process.env.AUDIT_CASE;
  const temp=mkdtempSync(join(tmpdir(),"chainlab-package-"));
  try{
   for(const name of ["ma60","ema20","williams14"]){
    process.env.AUDIT_CASE=name;const paths=casePaths();
    assert.ok(paths.proof.endsWith(`${name}.proof.json`));assert.ok(paths.proof.includes("chainlab"));
    requirePackage(paths.file,name);
    const changed=join(temp,`${name}.json`);writeFileSync(changed,readFileSync(paths.file,"utf8")+" ");
    assert.throws(()=>requirePackage(changed,name),/Package changed/);
   }
   process.env.AUDIT_CASE="unknown";assert.throws(casePaths,/AUDIT_CASE/);
  }finally{if(saved===undefined)delete process.env.AUDIT_CASE;else process.env.AUDIT_CASE=saved;rmSync(temp,{recursive:true,force:true});}
 });
 it("exercises submission journal and common proof validation on a simulated chain",async function(){
  const connection=await network.create("hardhatMainnet");
  const temp=mkdtempSync(join(tmpdir(),"chainlab-flow-"));
  try{
   const registry=await connection.ethers.deployContract("BacktestRegistry");await registry.waitForDeployment();
   let submitted:string|undefined;
   const proof=await anchorAuditWithPolicy(connection,"final_project/cases/ma60/audit_package.json",join(temp,"proof.json"),await registry.getAddress(),requireLocal,hash=>{submitted=hash;});
   assert.equal(submitted,proof.transaction_hash);
   await verifyAuditWithPolicy(connection,"final_project/cases/ma60/audit_package.json",proof,requireLocal);
   await assert.rejects(verifyAuditWithPolicy(connection,"final_project/cases/ema20/audit_package.json",proof,requireLocal),/fingerprint mismatch/);
  }finally{await connection.close();rmSync(temp,{recursive:true,force:true});}
 });
});
