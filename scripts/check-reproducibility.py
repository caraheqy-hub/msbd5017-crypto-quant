"""Run the current pipeline twice and verify byte-for-byte reproducibility.

Run from the repository root: python scripts/check-reproducibility.py
This regenerates local case outputs. It never commits, pushes, or sends transactions.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CASES = ("ma60", "ema20", "williams14")


def snapshot():
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT / "final_project/cases").rglob("*"))
            if p.suffix in {".json", ".csv", ".md"}}


def run_pipeline():
    env = dict(os.environ, PYTHONUTF8="1")
    for script in ("final_project/build_cases.py", "final_project/independent_replay.py",
                   "audit/verify_local.py"):
        print("Running:", script, flush=True)
        subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, env=env, check=True)


def main():
    # Fail visibly if an editor or checkout reintroduces platform-specific bytes.
    text_inputs = list((ROOT / "final_project").rglob("*.py"))
    text_inputs += list((ROOT / "final_project/input").rglob("*.yaml"))
    text_inputs += list((ROOT / "final_project/input").rglob("*.go"))
    for p in text_inputs:
        raw = p.read_bytes()
        raw.decode("utf-8")
        if b"\r" in raw or raw.startswith(b"\xef\xbb\xbf"):
            raise ValueError(f"Expected UTF-8 without BOM and LF: {p}")
    run_pipeline()
    first = snapshot()
    run_pipeline()
    second = snapshot()
    if first != second:
        raise ValueError("Repeated runs produced different file fingerprints")
    for name in second:
        if b"\r" in (ROOT / name).read_bytes():
            raise ValueError(f"Output is not LF: {name}")
    for case, expected in zip(CASES, (168, 390, 172)):
        summary = json.loads((ROOT / f"final_project/cases/{case}/case_summary.json").read_text(encoding="utf-8"))
        package_path = ROOT / f"final_project/cases/{case}/audit_package.json"
        actual = hashlib.sha256(package_path.read_bytes()).hexdigest()
        if summary["package_sha256"] != actual or summary["trades"] != expected:
            raise ValueError(f"Invalid package fingerprint or trade count: {case}")
    print(json.dumps({"repeated_runs_identical": True, "output_files": len(second),
                      "sha256": second}, indent=2), flush=True)


if __name__ == "__main__":
    main()
