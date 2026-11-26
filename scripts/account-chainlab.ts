import { network } from "hardhat";
import { formatEther } from "ethers";
import { manifest,requireChainlab } from "./chainlab-tools.js";
try {
 const connection=await network.create("chainlab");
 try {
  await requireChainlab(connection);
  const [signer]=await connection.ethers.getSigners();
  if(!signer) throw new Error("No signing account configured");
  const account=await signer.getAddress();
  if(account.toLowerCase()!==manifest.expected_account.toLowerCase()) throw new Error("Configured signer differs from preflight account");
  console.log("ACCOUNT CHECK PASSED:",account);
  console.log("Balance:",formatEther(await connection.ethers.provider.getBalance(account)));
  console.log("No signature or transaction was requested.");
 }finally{await connection.close();}
}catch(error){console.error(error);process.exitCode=1;}
