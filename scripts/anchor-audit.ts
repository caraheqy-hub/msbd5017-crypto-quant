import { network } from "hardhat";
import { anchorAudit, packageFile, proofFile } from "./audit-tools.js";
try {
  const address = process.env.REGISTRY_ADDRESS;
  if (!address) throw new Error("Set REGISTRY_ADDRESS to the locally deployed registry");
  const proof = await anchorAudit(await network.create(), packageFile(), proofFile(), address);
  console.log("AUDIT ANCHOR SUCCESS", proof);
} catch (error) { console.error(error); process.exitCode = 1; }
