"""Independent checks of DSH's reference portfolio assumptions; no files are modified."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

SCRIPT = Path(r"D:\argo_work\btc\portfolio_analysis.py")
spec = importlib.util.spec_from_file_location("portfolio_analysis", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
d = mod.load()


def inspect_sleeve(df, initial, deploy, fee=0.001, period=60):
    df = df.sort_values("time").reset_index(drop=True)
    close, op = df.close.to_numpy(float), df.open.to_numpy(float)
    ma = df.close.rolling(period).mean().to_numpy()
    cash, shares, pending = initial, 0.0, None
    negative_days = 0
    lowest_cash = initial
    first_fill = None
    for t in range(len(df)):
        if pending:
            side, qty = pending
            if side == "BUY":
                shares = qty
                cash -= qty * op[t] * (1 + fee)
            elif shares > 0:
                cash += shares * op[t] * (1 - fee)
                shares = 0
            if first_fill is None:
                first_fill = str(df.time.iloc[t].date())
            pending = None
        lowest_cash = min(lowest_cash, cash)
        negative_days += cash < -1e-8
        if not np.isnan(ma[t]):
            if close[t] > ma[t] and shares == 0 and cash > 0:
                qty = np.floor(cash * deploy / close[t] * 100) / 100
                if qty > 0:
                    pending = ("BUY", qty)
            elif close[t] < ma[t] and shares > 0:
                pending = ("SELL", 0)
    return first_fill, int(negative_days), float(lowest_cash)


def bh_from(df, first_tradeable, fee=0.001, initial=5000):
    df = df.sort_values("time").reset_index(drop=True)
    entry = float(df.open.iloc[first_tradeable])
    finish = float(df.close.iloc[-1])
    shares = initial / (entry * (1 + fee))
    return shares * finish * (1 - fee)


for deploy in (1.0, 0.45):
    for sym in ("BTCUSDT", "ETHUSDT"):
        df = d[d.symbol == sym]
        initial = 5000 if deploy == 1 else 4500
        print("sleeve", sym, "deploy", deploy, inspect_sleeve(df, initial, deploy))

for t in (0, 60):
    vals = [bh_from(d[d.symbol == s], t) for s in ("BTCUSDT", "ETHUSDT")]
    print("fee-adjusted BH start index", t, "date", str(d[d.symbol == "BTCUSDT"].sort_values("time").iloc[t].time.date()),
          "portfolio return", (sum(vals) / 10000 - 1))


def argo_nav():
    path = Path(r"D:\argo_work\btc\results_nextbar\20261118_164132\Search\03_ma60\btc_eth_daily\state.db\trades.parquet")
    trades = pq.read_table(path).to_pandas()
    trades["day"] = pd.to_datetime(trades.executed_at).dt.date
    prices = d.pivot(index="time", columns="symbol", values="close").sort_index()
    positions = {"BTCUSDT": 0.0, "ETHUSDT": 0.0}
    cash = 10000.0
    nav = []
    for day, row in prices.iterrows():
        for _, tr in trades[trades.day == day.date()].iterrows():
            positions[tr.symbol] += tr.executed_qty * (1 if tr.order_type == "BUY" else -1)
            cash = tr.balance
        nav.append(cash + sum(positions[s] * row[s] for s in positions))
    return np.array(nav), cash, positions


nav, final_cash, final_positions = argo_nav()
print("Argo MA60 actual shared-account NAV", mod.metrics(nav),
      "final_cash", final_cash, "final_positions", final_positions)
cut = int(len(nav) * 0.7)
dates = d[d.symbol == "BTCUSDT"].sort_values("time").time.reset_index(drop=True)
print("Argo 70/30 split", str(dates.iloc[cut].date()),
      "dev", mod.metrics(nav[:cut]), "tail", mod.metrics(nav[cut:]))
