"""Check order and cash integrity for every strategy in the fixed run."""

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


ROOT = Path(r"D:\argo_work\btc\results_fixed\20261118_170900")
for path in sorted(ROOT.rglob("orders.parquet")):
    strategy = path.parents[2].name
    orders = pq.read_table(path).to_pandas()
    trades = pq.read_table(path.with_name("trades.parquet")).to_pandas()
    statuses = orders.status.value_counts().to_dict()
    ids_match = set(orders.order_id) == set(trades.order_id)
    cash = 10000.0
    max_error = 0.0
    for _, trade in trades.iterrows():
        sign = 1 if trade.order_type == "BUY" else -1
        expected = cash - sign * trade.executed_qty * trade.executed_price - trade.commission
        max_error = max(max_error, abs(expected - trade.balance))
        cash = trade.balance
    print(strategy, {
        "orders": len(orders), "trades": len(trades), "statuses": statuses,
        "ids_match": ids_match, "min_cash": round(trades.balance.min(), 6),
        "max_cash_error": round(max_error, 10),
    })
