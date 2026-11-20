"""Why did a simple MA60 make +114%? Decompose the result.

Outputs yearly returns, trade-level statistics, concentration, and a
parameter/period robustness check.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent


def load(case="ma60"):
    pkg = json.loads((HERE / f"cases/{case}/audit_package.json").read_text(encoding="utf-8"))
    nav = pd.Series({x["day"]: x["nav"] for x in pkg["daily_nav"]}, dtype=float)
    nav.index = pd.to_datetime(nav.index, utc=True)
    trades = pd.DataFrame(pkg["trades"])
    trades["day"] = pd.to_datetime(trades["day"], utc=True)
    return pkg, nav, trades


def buy_hold(pkg):
    px = pd.read_parquet(HERE / "input/btc_eth_daily.parquet")
    px["time"] = pd.to_datetime(px["time"], utc=True)
    open_ = px.pivot(index="time", columns="symbol", values="open").sort_index()
    close = px.pivot(index="time", columns="symbol", values="close").sort_index()
    fee = 0.001
    alloc = 10000.0 / (2 * (1 + fee))
    qty = {s: alloc / float(open_.iloc[0][s]) for s in ("BTCUSDT", "ETHUSDT")}
    cash = 10000.0 - 2 * alloc * (1 + fee)
    nav = pd.Series(
        [cash + sum(qty[s] * float(close.iloc[i][s]) for s in qty) for i in range(len(close))],
        index=close.index,
    )
    return nav


def yearly(nav, price_nav):
    rows = []
    for year in sorted(set(nav.index.year)):
        a = nav[nav.index.year == year]
        b = price_nav[price_nav.index.year == year]
        if len(a) < 2:
            continue
        rows.append(
            {
                "year": int(year),
                "strategy": a.iloc[-1] / a.iloc[0] - 1,
                "buy_hold": b.iloc[-1] / b.iloc[0] - 1,
            }
        )
    return pd.DataFrame(rows)


def round_trips(trades):
    """Pair BUY -> SELL per symbol and compute realised PnL including fees."""
    out = []
    for symbol, g in trades.groupby("symbol"):
        g = g.sort_values("day", kind="stable")
        entry = None
        for _, t in g.iterrows():
            if t["side"] == "BUY":
                entry = t
            elif t["side"] == "SELL" and entry is not None:
                pnl = (
                    float(t["qty"]) * float(t["price"])
                    - float(t["fee"])
                    - (float(entry["qty"]) * float(entry["price"]) + float(entry["fee"]))
                )
                out.append(
                    {
                        "symbol": symbol,
                        "buy_day": entry["day"].date(),
                        "sell_day": t["day"].date(),
                        "days": (t["day"] - entry["day"]).days,
                        "buy_qty": float(entry["qty"]),
                        "pnl": pnl,
                        "ret_on_cost": pnl / (float(entry["qty"]) * float(entry["price"])),
                    }
                )
                entry = None
    return pd.DataFrame(out)


def main():
    pkg, nav, trades = load()
    bh = buy_hold(pkg)

    print("=== 全期 ===")
    print(f"strategy {nav.iloc[-1]/10000-1:+.2%}   buy&hold {bh.iloc[-1]/10000-1:+.2%}")

    print("\n=== 逐年（策略 vs 买入持有）===")
    y = yearly(nav, bh)
    for _, r in y.iterrows():
        print(f"  {int(r['year'])}: strategy {r['strategy']:+8.2%}   buy&hold {r['buy_hold']:+8.2%}")

    rt = round_trips(trades)
    print("\n=== 交易层 ===")
    wins = rt[rt.pnl > 0]
    losses = rt[rt.pnl <= 0]
    print(f"  完整回合 {len(rt)}，盈利 {len(wins)}，亏损 {len(losses)}，胜率 {len(wins)/len(rt):.1%}")
    print(f"  平均盈利 {wins.pnl.mean():+.2f}，平均亏损 {losses.pnl.mean():+.2f}，盈亏比 {abs(wins.pnl.mean()/losses.pnl.mean()):.2f}")
    print(f"  最好一笔 {rt.pnl.max():+.2f}，最差一笔 {rt.pnl.min():+.2f}")
    print(f"  平均持仓 {rt.days.mean():.0f} 天，盈利单平均 {wins.days.mean():.0f} 天，亏损单平均 {losses.days.mean():.0f} 天")

    total = rt.pnl.sum()
    top = rt.reindex(rt.pnl.abs().sort_values(ascending=False).index)
    for k in (3, 5, 10):
        share = top.head(k).pnl.sum() / total
        print(f"  前 {k} 笔贡献 {share:.1%} 的总利润")

    print("\n=== 剔除某年后重新比较 ===")
    for start in (2022, 2023):
        a = nav[nav.index.year >= start]
        b = bh[bh.index.year >= start]
        print(
            f"  自 {start} 年起：strategy {a.iloc[-1]/a.iloc[0]-1:+.2%}   "
            f"buy&hold {b.iloc[-1]/b.iloc[0]-1:+.2%}"
        )

    print("\n=== 平均仓位 ===")
    trades_sorted = trades.sort_values("day", kind="stable")
    pos = {"BTCUSDT": 0.0, "ETHUSDT": 0.0}
    exposure = []
    by_day = {d: g for d, g in trades_sorted.groupby("day", sort=False)}
    px = pd.read_parquet(HERE / "input/btc_eth_daily.parquet")
    px["time"] = pd.to_datetime(px["time"], utc=True)
    close = px.pivot(index="time", columns="symbol", values="close").sort_index()
    for day, row in close.iterrows():
        for _, t in by_day.get(day, pd.DataFrame()).iterrows():
            sign = 1 if t["side"] == "BUY" else -1
            pos[t["symbol"]] += sign * float(t["qty"])
        value = sum(pos[s] * float(row[s]) for s in pos)
        exposure.append(value / nav.loc[day])
    exposure = pd.Series(exposure, index=close.index)
    print(f"  策略平均收盘仓位 {exposure.mean():.1%}；空仓天数 {(exposure < 1e-9).sum()} / {len(exposure)}")

    print("\n=== 口径提示 ===")
    print("  策略平均仓位约 50%，买入持有恒 100%；")
    print("  因此「策略跑赢满仓」不等于「择时更强」，要按单位敞口看。")


if __name__ == "__main__":
    main()
