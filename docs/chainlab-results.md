# Verified chainlab results (2026-11-20)

All three v2 packages are anchored on chainlab and were independently verified.
The user submitted the transactions; this audit only performed read-only checks.

Registry: `0x35887245652F53eA72c8D6a9FD595c9bE78Cb284`
RPC: https://testnet.chainlab.fun
Chain ID: 31337; genesis is pinned in scripts/chainlab-manifest.json.

| Case | Record | Block | Original | Modified copy | Original again |
| --- | ---: | ---: | --- | --- | --- |
| ma60 | 9 | 21 | Pass | Rejected (exit 1) | Pass |
| ema20 | 10 | 22 | Pass | Rejected (exit 1) | Pass |
| williams14 | 11 | 23 | Pass | Rejected (exit 1) | Pass |

## Proofs and transaction IDs

### ma60

- Proof: [proofs/chainlab/ma60.proof.json](../proofs/chainlab/ma60.proof.json)
- Transaction: `0xf333c37597900c7aed191eb34fe96015876c2a1bfa7f924c60e10ecec90fbd36`
- Package SHA-256: `0xf77738d1a27e5e3b08688d8cb525a9ea4c74fa46b069cedf0797c394ab8cddec`

### ema20

- Proof: [proofs/chainlab/ema20.proof.json](../proofs/chainlab/ema20.proof.json)
- Transaction: `0xbeb31816e23804fa4e4a06f7924308376490c2f0af186eb20e5d3dee9ac10be3`
- Package SHA-256: `0x4f733e866989353c63674aa64071277411c6ac9451c0af1e997a7573790ae920`

### williams14

- Proof: [proofs/chainlab/williams14.proof.json](../proofs/chainlab/williams14.proof.json)
- Transaction: `0xe7e5314ceaded0c9eadc5dfbf009c1bebdc4bbd9ee8e7b2843f15201760476c3`
- Package SHA-256: `0x8e29d79d04e4c1cf21ec5ee8d18a3f223f1e96fc777eb7b7c9ae2b82451871a9`

## Evidence and next steps

All nine CLI checks passed; original package bytes are unchanged.
The chain remained at block 23 during this read-only verification.
No account was unlocked, and no transaction, commit or push was performed.
Raw CLI outputs are in evidence/2026-11-20-chainlab-final-verification.json.

Keep each confirmed proof with its exact audit package. Modified versions need
new fingerprints and separate proof files; do not overwrite the anchored version.
Remaining work is documentation/demo/report consolidation and a separate audit
of the reported Argo source revision and Go tests. Blockchain verification does
not replace that engine review or demonstrate future strategy profitability.
