"""将已审计的 MA60 组合与同区间买入持有基准作对照。

Usage:
    python regime_analysis.py --prices btc_eth_daily.parquet \
      --audit-package audit_package.json --output-dir output

第 t 天的行情状态只用截至 t-1 的 BTC 收盘价。对已选定策略作描述性评估，
不构成独立样本外测试。
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


INITIAL_CASH = 10000.0
FEE = 0.001
LOOKBACK = 30
THRESHOLD = 0.10


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_prices(path: Path) -> pd.DataFrame:
    data = pd.read_parquet(path)
    needed = {"time", "symbol", "open", "close"}
    if not needed.issubset(data.columns):
        raise ValueError(f"price file lacks {sorted(needed - set(data.columns))}")
    if data.duplicated(["time", "symbol"]).any():
        raise ValueError("duplicate time/symbol bars")
    open_ = data.pivot(index="time", columns="symbol", values="open")
    close = data.pivot(index="time", columns="symbol", values="close")
    symbols = ["BTCUSDT", "ETHUSDT"]
    if open_[symbols].isna().any().any() or close[symbols].isna().any().any():
        raise ValueError("missing BTC/ETH bars")
    bars = pd.DataFrame(index=close.index)
    for symbol in symbols:
        bars[f"{symbol}_open"] = open_[symbol]
        bars[f"{symbol}_close"] = close[symbol]
    bars.index = pd.to_datetime(bars.index, utc=True).strftime("%Y-%m-%d")
    return bars.sort_index()


def buy_hold_nav(bars: pd.DataFrame) -> pd.Series:
    """在首根日线开盘分别投入等额资金，买入费用计入预算。"""
    if len(bars) < 1:
        raise ValueError("at least one price date required")
    cash = INITIAL_CASH
    allocation = INITIAL_CASH / (2 * (1 + FEE))
    qty = {
        symbol: allocation / float(bars.iloc[0][f"{symbol}_open"])
        for symbol in ("BTCUSDT", "ETHUSDT")
    }
    cash -= 2 * allocation * (1 + FEE)
    nav = pd.Series(index=bars.index, dtype=float)
    for i in range(len(bars)):
        nav.iloc[i] = cash + sum(
            qty[s] * float(bars.iloc[i][f"{s}_close"]) for s in qty
        )
    return nav


def audit_nav(package: dict, bars: pd.DataFrame) -> pd.Series:
    entries = package["daily_nav"]
    nav = pd.Series({x["day"]: float(x["nav"]) for x in entries}, dtype=float)
    if len(nav) != len(entries) or not nav.index.equals(bars.index):
        raise ValueError("audit NAV dates do not exactly match price dates")
    if abs(nav.iloc[0] - INITIAL_CASH) > 1e-8:
        raise ValueError("unexpected starting capital")
    return nav


def replay_exposure_and_pnl(package: dict, bars: pd.DataFrame, nav: pd.Series) -> pd.DataFrame:
    """按成交账本重放开盘持仓，拆分价格盈亏和费用。"""
    trades = pd.DataFrame(package["trades"])
    positions = {"BTCUSDT": 0.0, "ETHUSDT": 0.0}
    by_day = {d: g for d, g in trades.groupby("day", sort=False)}
    records = []
    cash = INITIAL_CASH
    previous_nav = INITIAL_CASH
    previous_close = None
    for day, row in bars.iterrows():
        overnight_pnl = 0.0
        if previous_close is not None:
            overnight_pnl = sum(
                positions[s] * (float(row[f"{s}_open"]) - previous_close[s])
                for s in positions
            )
        fee = 0.0
        if day in by_day:
            for _, trade in by_day[day].iterrows():
                sign = 1 if trade["side"] == "BUY" else -1
                positions[trade["symbol"]] += sign * float(trade["qty"])
                cash = float(trade["cash_after"])
                fee += float(trade["fee"])
        open_value = sum(positions[s] * float(row[f"{s}_open"]) for s in positions)
        intraday_pnl = sum(
            positions[s] * (float(row[f"{s}_close"]) - float(row[f"{s}_open"]))
            for s in positions
        )
        close_value = sum(positions[s] * float(row[f"{s}_close"]) for s in positions)
        if abs(cash + close_value - float(nav.loc[day])) > 1e-6:
            raise ValueError(f"NAV cannot be reconciled from trades on {day}")
        price_pnl = overnight_pnl + intraday_pnl
        if previous_close is not None and abs(
            (float(nav.loc[day]) - previous_nav) - (price_pnl - fee)
        ) > 1e-6:
            raise ValueError(f"daily P&L cannot be reconciled on {day}")
        records.append(
            {
                "effective_open_exposure": open_value / previous_nav,
                "strategy_close_exposure": close_value / float(nav.loc[day]),
                "price_return_contribution": price_pnl / previous_nav,
                "fee_return_contribution": fee / previous_nav,
            }
        )
        previous_nav = float(nav.loc[day])
        previous_close = {s: float(row[f"{s}_close"]) for s in positions}
    return pd.DataFrame(records, index=bars.index)


def max_drawdown(nav: pd.Series) -> float:
    return float((nav / nav.cummax() - 1).min())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prices", type=Path, required=True)
    parser.add_argument("--audit-package", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    package = json.loads(args.audit_package.read_text(encoding="utf-8"))
    expected = package["data"]["sha256"]
    actual = sha256(args.prices)
    if actual != expected:
        raise ValueError(f"price SHA-256 mismatch: {actual} != {expected}")
    bars = load_prices(args.prices)
    strategy = audit_nav(package, bars)
    benchmark = buy_hold_nav(bars)
    attribution = replay_exposure_and_pnl(package, bars, strategy)

    table = pd.DataFrame(index=bars.index)
    table.index.name = "day"
    table["btc_close"] = bars["BTCUSDT_close"]
    table["strategy_nav"] = strategy
    table["benchmark_nav"] = benchmark
    table["strategy_return"] = strategy.pct_change()
    table["benchmark_return"] = benchmark.pct_change()
    table["active_return"] = table.strategy_return - table.benchmark_return
    for column in attribution:
        table[column] = attribution[column]
    # 第 t 天开盘时最新收盘价来自 t-1；过去 30 天收益比较 t-1 与 t-31。
    # 窗口不足的前期日期不分类。
    table["prior_30d_btc_return"] = (
        table.btc_close.shift(1) / table.btc_close.shift(LOOKBACK + 1) - 1
    )
    r = table.prior_30d_btc_return
    table["regime"] = np.select(
        [r > THRESHOLD, r < -THRESHOLD], ["上涨", "下跌"], default="震荡"
    )
    table.loc[r.isna(), "regime"] = "未分类"

    rows = []
    for label in ("上涨", "下跌", "震荡"):
        part = table.loc[table.regime == label]
        strategy_bps = float(part.strategy_return.mean() * 10000)
        benchmark_bps = float(part.benchmark_return.mean() * 10000)
        avg_exposure = float(part.strategy_close_exposure.mean())
        exposure_sum = float(part.effective_open_exposure.sum())
        # 净收益/实际开盘持仓总额；每日收益来自账本 NAV，分母按每日
        # 开盘成交后持仓计。避免拿事后收盘仓位作分母。
        per_unit = (
            float(part.strategy_return.sum() * 10000 / exposure_sum)
            if exposure_sum > 1e-9 else None
        )
        rows.append(
            {
                "regime": label,
                "days": int(len(part)),
                "strategy_mean_daily_bps": strategy_bps,
                "benchmark_mean_daily_bps": benchmark_bps,
                "active_mean_daily_bps": strategy_bps - benchmark_bps,
                "strategy_net_bps_per_unit_exposure": per_unit,
                "strategy_mean_effective_open_exposure": float(part.effective_open_exposure.mean()),
                "strategy_invested_days": int((part.effective_open_exposure > 1e-9).sum()),
                "strategy_mean_gross_price_daily_bps": float(
                    part.price_return_contribution.mean() * 10000
                ),
                "strategy_mean_fee_daily_bps": float(
                    part.fee_return_contribution.mean() * 10000
                ),
                "strategy_gross_price_bps_per_unit_exposure": (
                    float(part.price_return_contribution.sum() * 10000 / exposure_sum)
                    if exposure_sum > 1e-9 else None
                ),
                "strategy_fee_bps_per_unit_exposure": (
                    float(part.fee_return_contribution.sum() * 10000 / exposure_sum)
                    if exposure_sum > 1e-9 else None
                ),
                "strategy_positive_day_share": float((part.strategy_return > 0).mean()),
                "strategy_mean_close_exposure": avg_exposure,
            }
        )
    summary = {
        "input": {
            "price_sha256": actual,
            "audit_package_sha256": sha256(args.audit_package),
            "start": table.index[0],
            "end": table.index[-1],
            "total_days": len(table),
        },
        "method": {
            "regime": "BTC收盘价[t-1]/BTC收盘价[t-31]-1；高于10%为上涨，低于-10%为下跌，其余震荡",
            "regime_status": "描述性分析；策略和阈值并非在独立样本外确定",
            "benchmark": "初始资金BTC/ETH各50%，首根日线开盘买入，买入费10bp，此后持有；其敞口接近100%",
            "strategy": "审计包audit_package.json中的MA60共享账户NAV",
            "per_unit_exposure": (
                "策略单位敞口净收益=状态内每日净收益之和/每日开盘成交后有效敞口之和；"
                "价格收益与费用由逐笔账本重放并与每日NAV对账。"
                "基准资产权重与策略不同，单位敞口比较不是纯信号效应；低敞口状态数值不稳定"
            ),
        },
        "whole_period": {
            "strategy_return": float(strategy.iloc[-1] / strategy.iloc[0] - 1),
            "benchmark_return": float(benchmark.iloc[-1] / INITIAL_CASH - 1),
            "strategy_mdd": max_drawdown(strategy),
            "benchmark_mdd": max_drawdown(benchmark),
            "strategy_trades": len(package["trades"]),
        },
        "regimes": rows,
        "unclassified_days": int((table.regime == "未分类").sum()),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.output_dir / "regime_daily.csv", float_format="%.10f")
    (args.output_dir / "regime_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
