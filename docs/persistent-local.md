# Persistent local chain exercise (2026-11-20)

A background Hardhat node is listening only on http://127.0.0.1:8545.
Process ID: 94592. Logs and process metadata: build/local-node/.
The process was launched hidden; it can keep serving independent commands.
The chain is memory-backed: stopping/restarting the node clears its records.
No testnet transaction, Git commit or push was performed.

## Executed steps

1. Start the local node (the current one is already running).
2. Deploy the registry:

```powershell
bun hardhat ignition deploy ignition/modules/BacktestRegistry.ts --network localhost --deployment-id local-registry-20261120
```

3. Anchor the original MA60 package:

```powershell
$env:REGISTRY_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
$env:AUDIT_PACKAGE = "final_project/cases/ma60/audit_package.json"
$env:AUDIT_PROOF = "build/proofs/ma60.persistent-20261120.proof.json"
bun run anchor:local
```

This submission already succeeded at record 0, block 2. Do not repeat anchoring
with this proof path: the script intentionally refuses to overwrite a proof.

4. Verify in a separate command (safe to repeat):

```powershell
$env:AUDIT_PACKAGE = "final_project/cases/ma60/audit_package.json"
$env:AUDIT_PROOF = "build/proofs/ma60.persistent-20261120.proof.json"
bun run verify:local
```

5. A copy was made at build/proofs/ma60.persistent-20261120.tampered.json.
Only the copy's first trade quantity was changed from 0.10 to 0.11.

```powershell
$env:AUDIT_PACKAGE = "build/proofs/ma60.persistent-20261120.tampered.json"
bun run verify:local
```

It failed with fingerprint mismatch and exit code 1, as expected.
Reset AUDIT_PACKAGE to the original and verification passes again.
Verification does not send transactions; the node remained at block 2.

## Fix discovered during the exercise

Hardhat HTTP URLs are resolved configuration objects, not plain strings.
The local-network guard now awaits url.getUrl() and correctly permits loopback
URLs while rejecting remote hosts. Regression tests cover IPv4, localhost, IPv6,
the remote chainlab URL and a deceptive non-loopback hostname.
Build, typecheck and all 12 tests passed after this fix.

## Stopping the background node

When finished, verify the recorded PID still belongs to this node before stopping:

```powershell
Get-CimInstance Win32_Process -Filter "ProcessId=94592" | Select-Object ProcessId,CommandLine
# Only if the command line is this Hardhat local node:
Stop-Process -Id 94592
```

To start a new node later use `bun run node:local` and keep that terminal open.
Use a new deployment ID and proof path for a fresh node session; old proofs
refer to old chain state even when chain IDs and addresses happen to repeat.
The existing chainlab Counter deployment journal was not reused.

## EMA20 and Williams14 added to the same running node

Both packages were anchored and then verified in separate commands.
MA60 is record 0 / block 2; EMA20 is record 1 / block 3;
Williams14 is record 2 / block 4. All share the same genesis and contract.
Proofs are under build/proofs/<case>.persistent-20261120.proof.json.
All original package fingerprints remain unchanged. Verification is read-only.
For either case, set AUDIT_PACKAGE to final_project/cases/<case>/audit_package.json
and AUDIT_PROOF to its proof path, then run `bun run verify:local`.
Do not repeat anchoring over an existing proof. The node remains running, but
these records disappear when the node stops/restarts.
See evidence/2026-11-20-persistent-three-cases.json for the executed results.

## EMA20 and Williams14 tamper checks

Both originals passed before and after verification of separate modified copies.
EMA20 first quantity: 0.10 -> 0.11; Williams14 first quantity: 1.49 -> 1.50.
Each copy was rejected with fingerprint mismatch and exit code 1.
Original hashes still match their anchoring proofs. The local chain remains at
block 4; these checks sent no transactions. Copies are under build/proofs/.
See evidence/2026-11-20-persistent-tamper-checks.json for the executed results.
