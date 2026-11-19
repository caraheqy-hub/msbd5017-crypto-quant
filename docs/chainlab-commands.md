# Chainlab submission and verification commands

The old registry is reused: 0x35887245652F53eA72c8D6a9FD595c9bE78Cb284.
No contract deployment is needed. Local entry points remain local-only.
The new chainlab entry points pin the RPC URL, chain ID, genesis, registry,
expected signing account and the three reviewed audit-package hashes in
scripts/chainlab-manifest.json. No audit package or generator was modified.

## Step 1: read-only preflight (no password, no signature, no transaction)

```powershell
$env:AUDIT_CASE = "ma60"
bun run chainlab:check
```

Expected final output: CHAINLAB PREFLIGHT PASSED.
This disables configured accounts with a connection override and uses VoidSigner
for read-only simulation. It checks file bytes, network identity, registry,
existing records, balance, fee estimate and proof/pending file status.
The public account printed here has not been checked against your keystore yet.

## Step 2: check your configured account (no transaction)

```powershell
bun run chainlab:account
```

This may ask for your local keystore password. Enter it only in your terminal.
It loads the configured account, prints its public address and balance, and
checks that it is the expected account. It does not sign or send anything.

## Step 3: actual submission (USER EXECUTION ONLY)

Only after reviewing Step 1/2 and agreeing on the current package:

```powershell
$env:AUDIT_CASE = "ma60"
bun run chainlab:anchor
```

THIS COMMAND SENDS ONE TRANSACTION AND SPENDS TEST COINS.
It does not deploy a new contract. It refuses an existing proof, pending journal,
changed package, unexpected account/network, or matching record already on chain.
It prints the transaction hash immediately and saves a pending journal under
proofs/chainlab/. After confirmation it writes ma60.proof.json there.
If interrupted, keep the transaction hash and pending journal. Do not delete them
and blindly retry; inspect/recover the existing transaction and proof first.

## Step 4: verify (read-only, no keystore needed)

```powershell
Remove-Item Env:AUDIT_VERIFY_FILE -ErrorAction SilentlyContinue
bun run chainlab:verify
```

Verification checks network/genesis, registry, actual file SHA-256, stored record,
receipt status, block hash and matching event. No account or private key is loaded.
To check a separate modified copy, set AUDIT_VERIFY_FILE to that copy's path.
AUDIT_CASE still selects the original case's proof. Nonzero exit means failure.
Clear AUDIT_VERIFY_FILE afterwards to verify the original again.

Repeat in order for ema20 and williams14 by setting AUDIT_CASE accordingly.
All package/proof paths are derived from AUDIT_CASE; local AUDIT_PACKAGE,
AUDIT_PROOF and REGISTRY_ADDRESS variables do not affect these testnet scripts.
Local proofs are never used as testnet proof. Repository-relative input paths are
saved in confirmed testnet proofs for portability. Keep proofs with final files.

## Checks actually executed during preparation

- Local Solidity build and TypeScript typecheck passed.
- 15 local tests passed (8 Solidity, 7 Mocha), including policy, file mutation,
  proof validation and submission callback checks on simulated chains.
- The new MA60 chainlab preflight passed without loading an account.
- Actual chainlab anchor, account-unlock and verify commands were NOT executed.
  Current v2 packages have not been submitted to chainlab by this preparation.
- No Git commit or push was performed.
