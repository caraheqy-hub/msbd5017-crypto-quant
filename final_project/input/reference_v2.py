"""Reference v2: real shared cash, fee-inclusive checks, t+1 Open fills.

Reconciles per trade with results_fixed MA60 (day/side/qty/price/fee/cash) and
compares the daily NAV. Also runs fee and slippage sensitivity.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

DATA = Path(r"D:\argo_work\btc\data\btc_eth_daily.parquet")
RUN = Path(r"D:\argo_work\btc\results_utilfix\20261118_234959\Search\03_ma60\btc_eth_daily")
PERIOD = 60
DEPLOY = 0.45
FEE = 0.001

d = pq.read_table(DATA).to_pandas()
d["time"] = pd.to_datetime(d["time"], utc=True)
btc = d[d.symbol == "BTCUSDT"].sort_values("time").reset_index(drop=True)
eth = d[d.symbol == "ETHUSDT"].sort_values("time").reset_index(drop=True)


def run(fee=FEE, slip=0.0):
    n = len(btc)
    op_b, cl_b = btc.open.to_numpy(float), btc.close.to_numpy(float)
    op_e, cl_e = eth.open.to_numpy(float), eth.close.to_numpy(float)
    ma_b = pd.Series(cl_b).rolling(PERIOD).mean().to_numpy()
    ma_e = pd.Series(cl_e).rolling(PERIOD).mean().to_numpy()

    cash = 10000.0
    pos = {"BTCUSDT": 0.0, "ETHUSDT": 0.0}
    pend = {"BTCUSDT": None, "ETHUSDT": None}
    nav = np.empty(n)
    fills, rejects = [], 0

    for t in range(n):
        for sym, op, cl, ma in (("BTCUSDT", op_b[t], cl_b[t], ma_b[t]),
                                ("ETHUSDT", op_e[t], cl_e[t], ma_e[t])):
            p = pend[sym]
            if p is not None:
                side, qty = p
                if side == "BUY":
                    fp = op * (1 + slip)
                    cost = qty * fp
                    f = cost * fee
                    if cost + f > cash + 1e-9:
                        rejects += 1
                    else:
                        cash -= cost + f
                        pos[sym] += qty
                        fills.append((str(btc.time.iloc[t].date()), sym, "BUY", qty, fp, f, cash))
                elif pos[sym] > 0:
                    qty = pos[sym]
                    fp = op * (1 - slip)
                    proceeds = qty * fp
                    f = proceeds * fee
                    cash += proceeds - f
                    pos[sym] = 0.0
                    fills.append((str(btc.time.iloc[t].date()), sym, "SELL", qty, fp, f, cash))
                pend[sym] = None

            if not np.isnan(ma):
                if cl > ma and pos[sym] == 0 and cash > 1e-9:
                    qty = np.floor(cash * DEPLOY / cl * 100) / 100
                    if qty > 0:
                        pend[sym] = ("BUY", qty)
                elif cl < ma and pos[sym] > 0:
                    pend[sym] = ("SELL", 0)

        nav[t] = cash + pos["BTCUSDT"] * cl_b[t] + pos["ETHUSDT"] * cl_e[t]

    return nav, fills, rejects, cash, pos


def metrics(x):
    r = np.diff(x) / x[:-1]
    std = np.std(r, ddof=1)
    peak = np.maximum.accumulate(x)
    return dict(ret=x[-1] / x[0] - 1, sharpe=np.mean(r) / std * np.sqrt(365), mdd=np.min(x / peak - 1))


def argo_nav():
    tr = pq.read_table(RUN / "state.db" / "trades.parquet").to_pandas()
    tr["day"] = pd.to_datetime(tr.executed_at).dt.date.astype(str)
    px = d.pivot(index="time", columns="symbol", values="close").sort_index()
    pos = {"BTCUSDT": 0.0, "ETHUSDT": 0.0}
    cash = 10000.0
    nav = []
    for day, row in px.iterrows():
        for _, t in tr[tr.day == day.date().isoformat()].iterrows():
            pos[t.symbol] += t.executed_qty * (1 if t.order_type == "BUY" else -1)
            cash = t.balance
        nav.append(cash + sum(pos[s] * row[s] for s in pos))
    return tr, np.array(nav)


def main():
    nav, fills, rejects, cash, pos = run()
    atr, anav = argo_nav()

    print("=== reference ===", metrics(nav), "rejects", rejects, "final_cash", round(cash, 2), pos)
    print("=== argo ===", metrics(anav))

    ref = pd.DataFrame(fills, columns=["day", "symbol", "side", "qty", "price", "fee", "cash"])
    ref = ref.rename(columns={"price": "ref_price", "qty": "ref_qty", "fee": "ref_fee", "cash": "ref_cash"})
    atr = atr.rename(columns={"order_type": "side"})
    m = atr.merge(ref, on=["day", "symbol", "side"], suffixes=("_argo", "_ref"))
    print(f"\ntrades argo={len(atr)} ref={len(ref)} matched={len(m)}")

    for col_a, col_r, name in (("executed_price", "ref_price", "price"),
                               ("executed_qty", "ref_qty", "qty"),
                               ("commission", "ref_fee", "fee"),
                               ("balance", "ref_cash", "cash")):
        diff = (m[col_a] - m[col_r]).abs()
        bad = m[diff > 1e-6]
        print(f"{name}: max|d|={diff.max():.6g} mismatches(>1e-6)={len(bad)}")
        if len(bad):
            print(bad[["day", "symbol", "side", col_a, col_r]].head(8).to_string(index=False))

    dnav = np.abs(nav - anav)
    print(f"\nNAV: max|d|={dnav.max():.6g}  final argo={anav[-1]:.2f} ref={nav[-1]:.2f}")

    print("\n=== fee sensitivity (fixed semantics) ===")
    for fee in (0.001, 0.002, 0.004):
        nv, fl, rj, _, _ = run(fee=fee)
        mm = metrics(nv)
        print(f"  {fee*10000:.0f}bp: ret={mm['ret']:+.1%} sharpe={mm['sharpe']:.2f} mdd={mm['mdd']:+.1%} rejects={rj}")

    print("\n=== slippage sensitivity (fee 10bp) ===")
    for slip in (0.0, 0.001, 0.002, 0.005):
        nv, fl, rj, _, _ = run(slip=slip)
        mm = metrics(nv)
        print(f"  slip {slip*10000:.0f}bp: ret={mm['ret']:+.1%} sharpe={mm['sharpe']:.2f} mdd={mm['mdd']:+.1%} rejects={rj}")


if __name__ == "__main__":
    main()
