# Chainlab read-only preflight (2026-11-20)

All three current v2 audit packages passed raw file hash, local proof hash,
summary hash, source/data fingerprint, trade-count, NAV-count and Merkle checks.
No audit package was regenerated or edited.

RPC: https://testnet.chainlab.fun
Chain ID: 31337. Genesis matches the historical testnet proof, distinguishing it
from the separate local node even though both have chain ID 31337.

Public account from the Counter deployment journal:
0x715790f90491a4f8b843c52ac182e1d6bea43a88
Balance snapshot: 0.998113380382474488 native test-coin units (18 decimals).
No private key was loaded. Current keystore ownership was not verified.

Reusable old registry: 0x35887245652F53eA72c8D6a9FD595c9bE78Cb284
It holds 9 records. Historical record 3 hash and receipt match the saved proof.
No current v2 package fingerprint was found among these 9 records.
Read-only simulations for all three submissions succeeded. Each estimated
95,770 gas; total estimated fees were 0.00033351971128782 native test-coin units.
Fees can change. Simulations do not write state or reserve record IDs.

The default development bytecode did not match. Inspection of the archived
deployment input showed optimizer enabled / 200 runs and matching Solidity source.
A local production-profile compilation produced identical executable bytecode;
only compilation metadata differs. The existing registry can be reused.

Before any actual submission: agree on final packages with the teammate, confirm
the signing account locally, and explicitly prepare chainlab-capable submission
and proof validation. Current audit tools still intentionally reject remote RPCs.
Use separate testnet proof paths and never reuse local proofs as testnet evidence.

No deployment, submission, signature, transfer, Git commit or push was performed.
Full results: evidence/2026-11-20-chainlab-preflight.json.
