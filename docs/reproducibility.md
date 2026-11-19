# File bytes and reproducibility

The current pipeline uses UTF-8 without BOM and LF line endings. `.gitattributes`
keeps current source, input configuration, and generated case files in LF even
when Git's global core.autocrlf setting is true. JSON writers specify UTF-8 and
newline="\n"; CSV generation specifies lineterminator="\n".
SHA-256 always hashes actual bytes. Verification never ignores changes.

## Historical exception

`audit/audit_package.json` is the original MA60 v1 package. Its manifest hashes
the CRLF representation (SHA-256 begins 4c676f12). A specific Git attribute keeps
that representation on checkout. Original file bytes and manifest are unchanged.
Do not use that old package or its fingerprints as evidence for current v2 cases.

## Verify locally

Run from the repository root with the requirements installed:

```powershell
python scripts/check-reproducibility.py
```

This runs the build, independent replay and historical integrity check twice.
It compares all 15 generated JSON/CSV/Markdown outputs byte for byte, checks LF,
package hashes and trade counts, and exits nonzero on failure. It rewrites local
outputs; it never commits, pushes or sends transactions. CRLF/BOM in current
source inputs is rejected rather than silently ignored.

## Version change and evidence

The generator was edited to specify encoding and newlines, so its source hash
changed. The original case-specific YAML fingerprints represented CRLF bytes;
these inputs now use LF, and their raw-byte fingerprints changed as well.
The only changed package fields are provenance.builder_sha256 and
provenance.indicator_config_sha256. Transaction records, daily NAV, parsed
strategy configuration, market data and both Merkle roots match the baseline.
The packages remain schema v2 with new recorded provenance and whole-file hashes.
The original packages remain in Git history; no commit was created. Use the new
hashes for future anchoring only after teammates agree on the revised files.

See evidence/2026-11-20-reproducibility.json for baseline and old/new fingerprints.
Two complete runs passed on Windows / Python 3.11.5. Linux/macOS were not run;
dependency-version differences beyond line endings may require verification.
Changing generator source in future intentionally changes its recorded hash.
