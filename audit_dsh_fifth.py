"""Independent reconciliation of the fifth Argo MA60 run."""

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


RUN = Path(r"D:\argo_work\btc\results_fixed\20261118_170900\Search\03_ma60\btc_eth_daily")
DATA = Path(r"D:\argo_work\btc\data\btc_eth_daily.parquet")

trades = pq.read_table(RUN / "state.db/trades.parquet").to_pandas()
orders = pq.read_table(RUN / "state.db/orders.parquet").to_pandas()
prices = pq.read_table(DATA).to_pandas()
prices["time"] = pd.to_datetime(prices["time"], utc=True)
close = prices.pivot(index="time", columns="symbol", values="close").sort_index()
trades["day"] = pd.to_datetime(trades["executed_at"], utc=True).dt.normalize()

assert orders.order_id.is_unique and trades.order_id.is_unique
assert set(orders.order_id) == set(trades.order_id)
assert (orders.status == "FILLED").all()
assert (trades.balance >= -1e-8).all()

cash = 10000.0
positions = {symbol: 0.0 for symbol in close.columns}
nav = []
cash_errors = []
for day, bar in close.iterrows():
    for _, trade in trades.loc[trades.day == day].iterrows():
        signed = 1 if trade.order_type == "BUY" else -1
        expected_cash = cash - signed * trade.executed_qty * trade.executed_price - trade.commission
        cash_errors.append(abs(expected_cash - trade.balance))
        cash = trade.balance
        positions[trade.symbol] += signed * trade.executed_qty
    nav.append(cash + sum(positions[symbol] * bar[symbol] for symbol in positions))

nav = np.asarray(nav)
ret = np.diff(nav) / nav[:-1]
peak = np.maximum.accumulate(nav)
cut = int(len(nav) * 0.7)
print({
    "bars": len(close), "trades": len(trades), "orders": len(orders),
    "failed_orders": int((orders.status != "FILLED").sum()),
    "min_trade_cash": float(trades.balance.min()),
    "max_cash_reconciliation_error": max(cash_errors),
    "negative_position_count": sum(q < -1e-8 for q in positions.values()),
    "initial_nav": float(nav[0]), "final_nav": float(nav[-1]),
    "return": float(nav[-1] / nav[0] - 1),
    "daily_sharpe_365": float(ret.mean() / ret.std(ddof=1) * np.sqrt(365)),
    "mdd": float(np.min(nav / peak - 1)),
    "tail_30pct_return": float(nav[-1] / nav[cut] - 1),
    "last_cash": cash, "last_positions": positions,
})
