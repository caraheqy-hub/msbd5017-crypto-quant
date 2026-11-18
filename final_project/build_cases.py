"""Build audit packages for the three candidate strategies.

All three use the same method: replay the engine's trade ledger in its original
order (stable), reconcile cash per trade, and mark positions to close. The
package schema matches audit/audit_package.json so regime_analysis.py can read it.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(r"D:\argo_work\btc\results_utilfix\20261118_234959\Search")
DATA = Path(r"D:\argo_work\btc\data\btc_eth_daily.parquet")
OUT = Path(r"D:\Desktop\hkust_sem1\5017\crypto_project\final_project\cases")
INITIAL = 10000.0

CASES = {
    "ma60": ("03_ma60", "MA60 trend"),
    "ema20": ("04_ema20", "EMA20 trend"),
    "williams14": ("06_williams14", "Williams %R 14"),
}

px = pq.read_table(DATA).to_pandas()
px["time"] = pd.to_datetime(px["time"], utc=True)
close = px.pivot(index="time", columns="symbol", values="close").sort_index()
open_ = px.pivot(index="time", columns="symbol", values="open").sort_index()
data_sha = hashlib.sha256(DATA.read_bytes()).hexdigest()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def leaf(obj) -> str:
    return sha256_hex(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def merkle_root(leaves) -> str:
    if not leaves:
        return sha256_hex(b"")
    level = [bytes.fromhex(h) for h in leaves]
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [hashlib.sha256(a + b).digest() for a, b in zip(level[::2], level[1::2])]
    return level[0].hex()


def build(name: str, dirname: str, label: str):
    trades_path = ROOT / dirname / "btc_eth_daily" / "state.db" / "trades.parquet"
    tr = pq.read_table(trades_path).to_pandas()
    tr["day"] = pd.to_datetime(tr["executed_at"]).dt.strftime("%Y-%m-%d")

    cash = INITIAL
    pos = {"BTCUSDT": 0.0, "ETHUSDT": 0.0}
    nav = []
    entries = []
    for day, row in close.iterrows():
        day_str = day.strftime("%Y-%m-%d")
        for _, t in tr[tr["day"] == day_str].iterrows():
            qty = float(t["executed_qty"])
            price = float(t["executed_price"])
            fee = float(t["commission"])
            if t["order_type"] == "BUY":
                cash = cash - qty * price - fee
                pos[t["symbol"]] += qty
            else:
                cash = cash + qty * price - fee
                pos[t["symbol"]] -= qty
            if abs(cash - float(t["balance"])) > 1e-6:
                raise ValueError(f"{name} cash mismatch on {day_str} {t['symbol']} {t['order_type']}")
            entries.append({
                "day": day_str,
                "symbol": t["symbol"],
                "side": t["order_type"],
                "qty": round(qty, 10),
                "price": round(price, 10),
                "fee": round(fee, 10),
                "cash_after": round(cash, 10),
            })
        nav.append(round(cash + sum(pos[s] * float(row[s]) for s in pos), 10))

    daily_nav = [{"day": d.strftime("%Y-%m-%d"), "nav": v} for d, v in zip(close.index, nav)]
    trade_leaves = [leaf(x) for x in entries]
    nav_leaves = [leaf(x) for x in daily_nav]

    package = {
        "schema": "msbd5017.audit.v1",
        "experiment": {
            "name": name,
            "strategy": label,
            "period": {"start": daily_nav[0]["day"], "end": daily_nav[-1]["day"]},
            "symbols": ["BTCUSDT", "ETHUSDT"],
            "initial_capital": INITIAL,
            "fee_per_side": 0.001,
            "execution": "signal at bar t close, fill at bar t+1 open",
            "portfolio": "single shared cash account",
        },
        "code_commit": "23f1418",
        "data": {"path": DATA.name, "sha256": data_sha},
        "trades": entries,
        "trades_merkle_root": merkle_root(trade_leaves),
        "daily_nav": daily_nav,
        "nav_merkle_root": merkle_root(nav_leaves),
    }

    case_dir = OUT / name
    case_dir.mkdir(parents=True, exist_ok=True)
    text = json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    pkg = case_dir / "audit_package.json"
    pkg.write_text(text, encoding="utf-8")

    nav_arr = np.array(nav)
    peak = np.maximum.accumulate(nav_arr)
    summary = {
        "case": name,
        "label": label,
        "return": float(nav_arr[-1] / INITIAL - 1),
        "mdd": float(np.min(nav_arr / peak - 1)),
        "trades": len(entries),
        "final_nav": float(nav_arr[-1]),
        "package_sha256": sha256_hex(pkg.read_bytes()),
        "trades_merkle_root": package["trades_merkle_root"],
        "nav_merkle_root": package["nav_merkle_root"],
    }
    (case_dir / "case_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    for name, (dirname, label) in CASES.items():
        build(name, dirname, label)
