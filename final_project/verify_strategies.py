"""Recompute shared-account return / MDD / trades for every strategy run.

Trades sharing a timestamp must keep their original order: the ledger's
`balance` is the post-trade cash, so an unstable sort silently corrupts the
cash sequence and the NAV curve. We sort stably and reconcile cash per trade.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(r"D:\argo_work\btc\results_utilfix\20261118_234959\Search")
DATA = Path(r"D:\argo_work\btc\data\btc_eth_daily.parquet")
INITIAL = 10000.0

px = pq.read_table(DATA).to_pandas()
px["time"] = pd.to_datetime(px["time"], utc=True)
close = px.pivot(index="time", columns="symbol", values="close").sort_index()


def evaluate(strategy_dir: Path):
    tr = pq.read_table(strategy_dir / "state.db" / "trades.parquet").to_pandas()
    tr["day"] = pd.to_datetime(tr["executed_at"]).dt.tz_localize("UTC").dt.tz_convert("UTC")

    # Keep the original intra-timestamp order; the default quicksort does not.
    tr = tr.sort_values("day", kind="stable").reset_index(drop=True)

    pos = {"BTCUSDT": 0.0, "ETHUSDT": 0.0}
    cash = INITIAL
    nav = []
    for day, row in close.iterrows():
        for _, t in tr[tr["day"] == day].iterrows():
            qty = float(t["executed_qty"])
            price = float(t["executed_price"])
            fee = float(t["commission"])
            notional = qty * price
            if t["order_type"] == "BUY":
                cash = cash - notional - fee
                pos[t["symbol"]] += qty
            else:
                cash = cash + notional - fee
                pos[t["symbol"]] -= qty
            if abs(cash - float(t["balance"])) > 1e-6:
                raise ValueError(
                    f"cash mismatch at {day} {t['symbol']} {t['order_type']}: "
                    f"rebuilt {cash:.10f} != ledger {float(t['balance']):.10f}"
                )
        nav.append(cash + sum(pos[s] * float(row[s]) for s in pos))

    nav = np.array(nav)
    peak = np.maximum.accumulate(nav)
    return {
        "ret": nav[-1] / INITIAL - 1,
        "mdd": float(np.min(nav / peak - 1)),
        "trades": len(tr),
        "final": nav[-1],
    }


for d in sorted(ROOT.iterdir()):
    trades = d / "btc_eth_daily" / "state.db" / "trades.parquet"
    if not trades.exists():
        continue
    r = evaluate(d / "btc_eth_daily")
    print(f"{d.name:16s} ret={r['ret']:+8.2%} mdd={r['mdd']:+7.2%} trades={r['trades']:4d} final={r['final']:.2f}")
