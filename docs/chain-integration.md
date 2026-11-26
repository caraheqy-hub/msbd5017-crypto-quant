# Local Hardhat registry integration

## What was added

BacktestRegistry.sol and its Ignition module were imported from
https://github.com/Adazhangdada/group27_trade at commit
`afd1a12aea32862719fb65094339335393635ad1`.
The contract logic and ABI are unchanged; source line endings are LF.
Counter remains an initialization example. Its chainlab address is not a registry.
Existing Hardhat dependencies, bun.lock, network profiles and deployment records
are retained. No dependencies were added by this integration.

The shared audit tools hash the actual file bytes with SHA-256, submit a hash,
save a proof, and verify the file against the stored hash and transaction event.
Proofs include chain ID, genesis hash, contract, record, transaction, block, signer
and file hash. Existing proof files are not overwritten. These audit tools reject
remote networks before RPC/signing; chainlab remains configured for future work,
but no testnet operation was executed as part of this integration.

## Quick local check

From the repository root with Node 24 and Bun installed:

```powershell
bun install --frozen-lockfile
bun run build
bun run typecheck
bun run test
bun run demo:local
```

For the full Hardhat suite use `bun run test` (not Bun's built-in `bun test`).
The first line is needed only for a fresh checkout; it was not needed here.
The demo explicitly creates an in-process `hardhatMainnet` simulated connection.
It deploys the registry, submits all three v2 packages, verifies originals,
changes a trade quantity in separate copies, verifies detection, and verifies
originals again. It writes evidence under `build/local-demo/<UTC timestamp>/`.
No private key or testnet funds are required. Original packages are never edited.
The simulation disappears when the process exits. Saved proofs describe that
local demonstration; they are not permanent testnet evidence.

## Separate commands with a persistent local node

Use this only when you want to anchor and verify in separate commands.
In terminal A, run `bun run node:local` and keep it open.
In terminal B, deploy locally:

```powershell
bun hardhat ignition deploy ignition/modules/BacktestRegistry.ts --network localhost --deployment-id local-registry
```

The custom deployment ID keeps the local journal separate from the existing
chainlab Counter journal (both networks can use chain ID 31337).
Set the returned registry address and input/output paths in terminal B:

```powershell
$env:REGISTRY_ADDRESS = "<local registry address printed by deployment>"
$env:AUDIT_PACKAGE = "final_project/cases/ma60/audit_package.json"
$env:AUDIT_PROOF = "build/proofs/ma60.local.proof.json"
bun run anchor:local
bun run verify:local
```

To verify a tampered copy, change AUDIT_PACKAGE to the copy while keeping the
original proof; verification exits nonzero on mismatch. The default package is
current MA60 v2, not historical audit/audit_package.json. Choose separate proof
paths for each package. Restarting the local node discards its previous state.
These persistent-node commands were subsequently exercised successfully.
See persistent-local.md and evidence/2026-11-20-persistent-local.json.

## Verified results

Build and TypeScript checking passed. All 12 tests passed (8 Solidity, 4 Mocha),
including 256-run fuzz tests, tampered package, wrong network/genesis/transaction,
proof overwrite protection, and remote-network rejection. Three-case demo passed;
all originals stayed unchanged. See evidence/2026-11-20-chain-integration.json.
No commit, Git push or testnet transaction was executed by this integration.
