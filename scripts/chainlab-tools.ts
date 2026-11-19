import { network } from "hardhat";
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { formatEther, VoidSigner } from "ethers";
import { fileHash } from "./audit-tools.js";
type Connection = Awaited<ReturnType<typeof network.create>>;
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const manifest = JSON.parse(readFileSync(resolve(root, "scripts/chainlab-manifest.json"), "utf8")) as {
 rpc_url: string; chain_id: string; genesis_hash: string; contract_address: string; expected_account: string; packages: Record<string,string>;
};
export function casePaths() {
 const name=process.env.AUDIT_CASE ?? "ma60";
 if (!Object.hasOwn(manifest.packages,name)) throw new Error("AUDIT_CASE must be ma60, ema20 or williams14");
 return {name,file:resolve(root,`final_project/cases/${name}/audit_package.json`),proof:resolve(root,`proofs/chainlab/${name}.proof.json`),pending:resolve(root,`proofs/chainlab/${name}.pending.json`)};
}
export function requirePackage(file:string,name:string) {
 const hash=fileHash(file);
 if(hash!=="0x"+manifest.packages[name]) throw new Error("Package changed since preflight; review its version before anchoring");
 return hash;
}
export async function requireChainlab(connection:Connection):Promise<void> {
 const c=connection.networkConfig;
 if(connection.networkName!=="chainlab" || c.type!=="http" || await c.url.getUrl()!==manifest.rpc_url) throw new Error("Expected the configured chainlab endpoint");
 const p=connection.ethers.provider;
 if((await p.getNetwork()).chainId.toString()!==manifest.chain_id) throw new Error("Wrong chainlab chain ID");
 if((await p.getBlock(0))?.hash!==manifest.genesis_hash) throw new Error("Wrong chainlab genesis; stop and review");
 if(await p.getCode(manifest.contract_address)==="0x") throw new Error("Old registry missing");
}
export async function readOnlyConnection() {
 return network.create({network:"chainlab",override:{accounts:[]}});
}
export async function preflight(connection:Connection) {
 await requireChainlab(connection);
 const paths=casePaths(); const hash=requirePackage(paths.file,paths.name);
 if(existsSync(paths.pending)) throw new Error("Pending transaction journal exists; resolve it before retrying");
 const {ethers}=connection;
 const registry=await ethers.getContractAt("BacktestRegistry",manifest.contract_address,new VoidSigner(manifest.expected_account,ethers.provider));
 const count=await registry.recordCount();
 if(count>1000n) throw new Error("More than 1000 records; review before scanning");
 let existingRecord:string|null=null;
 for(let i=0n;i<count;i++) if((await registry.getHash(i)).toLowerCase()===hash.toLowerCase()){existingRecord=i.toString();break;}
 await registry.anchorBacktest.staticCall(hash);
 const gas=await registry.anchorBacktest.estimateGas(hash);
 const fee=await ethers.provider.getFeeData(); const price=fee.maxFeePerGas??fee.gasPrice;
 if(price===null) throw new Error("Fee estimate unavailable");
 const budget=gas*120n/100n*price; const balance=await ethers.provider.getBalance(manifest.expected_account);
 console.log("Case:",paths.name);console.log("Registry:",manifest.contract_address);
 console.log("Public account (keystore not checked):",manifest.expected_account);
 console.log("SHA-256:",hash);console.log("Balance (native test coins):",formatEther(balance));
 console.log("Estimated budget with 20% gas margin:",formatEther(budget));
 console.log("Existing record:",existingRecord??"none");console.log("Proof file:",paths.proof);console.log("Existing proof file:",existsSync(paths.proof));
 if(balance<budget) throw new Error("Insufficient estimated balance");
 return {paths,hash,existingRecord};
}
