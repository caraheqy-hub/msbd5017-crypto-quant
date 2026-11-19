import { preflight,readOnlyConnection } from "./chainlab-tools.js";
try {
 const connection=await readOnlyConnection();
 try {await preflight(connection);console.log("CHAINLAB PREFLIGHT PASSED: read-only; no transaction signed or sent.");}
 finally {await connection.close();}
}catch(error){console.error(error);process.exitCode=1;}
