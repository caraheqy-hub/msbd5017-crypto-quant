"""记录一次实验，并比较两次实验的差异。

运行：
    python final_project/run_record.py record
    python final_project/run_record.py compare <A.json> <B.json>
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(case: str) -> None:
    config = json.loads((HERE / f"input/ledgers/{case}.yaml").read_text(encoding="utf-8"))
    data = HERE / "input/btc_eth_daily.parquet"
    summary = json.loads((HERE / f"cases/{case}/regime_summary.json").read_text(encoding="utf-8"))
    wp = summary["whole_period"]

    payload = {
        "case": case,
        "config": config,
        "data_sha256": sha256_file(data),
        "code_commit": "23f1418",
    }
    run_id = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]

    record = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **payload,
        "results": {
            "return": wp["strategy_return"],
            "mdd": wp["strategy_mdd"],
            "trades": wp["strategy_trades"],
        },
    }

    RUNS.mkdir(exist_ok=True)
    (RUNS / f"{case}-{run_id}.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"{case}: run_id={run_id} return={wp['strategy_return']:+.2%} "
        f"mdd={wp['strategy_mdd']:+.2%} trades={wp['strategy_trades']}"
    )


def compare(a: Path, b: Path) -> None:
    ra = json.loads(a.read_text(encoding="utf-8"))
    rb = json.loads(b.read_text(encoding="utf-8"))
    print(f"A: {ra['case']} {ra['run_id']}  ({ra['created_at']})")
    print(f"B: {rb['case']} {rb['run_id']}  ({rb['created_at']})")
    for key in ("return", "mdd"):
        va, vb = ra["results"][key], rb["results"][key]
        print(f"  {key}: {va:+.2%} -> {vb:+.2%}  (Δ {vb - va:+.2%})")
    print(f"  trades: {ra['results']['trades']} -> {rb['results']['trades']}")
    for key in ("config", "data_sha256", "code_commit"):
        if ra[key] != rb[key]:
            print(f"  {key} changed: {ra[key]} -> {rb[key]}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("用法: record | compare <A.json> <B.json>")
    if sys.argv[1] == "record":
        for case in ("ma60", "ema20", "williams14"):
            record(case)
    elif sys.argv[1] == "compare":
        compare(Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        raise SystemExit("未知子命令")
