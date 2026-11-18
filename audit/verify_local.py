"""Chain-free check of the audit package: hash match and tamper detection."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE / "audit_package.json"
MAN = HERE / "audit_manifest.json"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    manifest = json.loads(MAN.read_text(encoding="utf-8"))
    raw = PKG.read_bytes()
    local = sha256_hex(raw)

    print("package sha256 :", local)
    print("manifest sha256:", manifest["package_sha256"])
    print("match          :", local == manifest["package_sha256"])
    if local != manifest["package_sha256"]:
        raise SystemExit("审计包与本地清单不匹配")

    # Tamper with one trade and show the hash changes, so verification fails.
    obj = json.loads(raw)
    obj["trades"][0]["qty"] = round(obj["trades"][0]["qty"] + 0.01, 10)
    tampered = (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    tampered_hash = sha256_hex(tampered)

    print("\ntampered sha256:", tampered_hash)
    print("tamper detected:", tampered_hash != manifest["package_sha256"])


if __name__ == "__main__":
    main()
