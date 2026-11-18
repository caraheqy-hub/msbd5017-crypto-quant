"""先从价格和配置独立生成交易，再读取 Argo 账本逐笔比较。

运行：python final_project/independent_replay.py
EMA 复现当前 Argo 的有限历史窗口初始化规则，非无限历史 EMA。
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SYMBOLS = ["BTCUSDT", "ETHUSDT"]


def indicator_values(frame, kind, period):
    close = frame.close.to_numpy(float)
    if kind == "ma":
        return frame.close.rolling(period).mean().to_numpy()
    if kind == "williams":
        high = frame.high.rolling(period).max().to_numpy()
        low = frame.low.rolling(period).min().to_numpy()
        width = high - low
        return np.divide(-100 * (high - close), width,
                         out=np.zeros(len(close)), where=width != 0)
    values = np.full(len(close), np.nan)
    for t in range(period - 1, len(close)):
        # 数据源要求完整窗口；不足3倍周期时返回错误，EMA退回仅period根。
        length = period * 3 if t + 1 >= period * 3 else period
        window = close[t - length + 1:t + 1]
        ema = sum(window[:period]) / period
        alpha = 2 / (period + 1)
        for price in window[period:]:
            ema = price * alpha + ema * (1 - alpha)
        values[t] = ema
    return values


def simulate(data, config):
    frames = {s: data[data.symbol == s].sort_values("time").reset_index(drop=True)
              for s in SYMBOLS}
    values = {s: indicator_values(frames[s], config["kind"], config["period"])
              for s in SYMBOLS}
    cash = 10000.0
    positions = dict.fromkeys(SYMBOLS, 0.0)
    pending = dict.fromkeys(SYMBOLS)
    fills, nav = [], []
    rejects = 0
    for t in range(len(frames[SYMBOLS[0]])):
        for symbol in SYMBOLS:
            bar = frames[symbol].iloc[t]
            day = pd.Timestamp(bar.time).strftime("%Y-%m-%d")
            order = pending[symbol]
            pending[symbol] = None
            if order:
                side, qty = order
                price = float(bar.open)
                if side == "SELL":
                    qty = positions[symbol]
                fee = qty * price * .001
                if side == "BUY" and qty * price + fee > cash + 1e-9:
                    rejects += 1
                else:
                    sign = 1 if side == "BUY" else -1
                    cash -= sign * qty * price + fee
                    positions[symbol] += sign * qty
                    fills.append(dict(day=day, symbol=symbol, side=side, qty=qty,
                                      price=price, fee=fee, cash_after=cash))
            value = values[symbol][t]
            if t < config["period"] - 1 or np.isnan(value):
                continue
            if config["kind"] == "williams":
                buy, sell = value < config["oversold"], value > config["overbought"]
            else:
                buy, sell = bar.close > value, bar.close < value
            if buy and positions[symbol] == 0:
                qty = math.floor(cash * .45 / float(bar.close) * 100) / 100
                if qty > 0:
                    pending[symbol] = ("BUY", qty)
            elif sell and positions[symbol] > 0:
                pending[symbol] = ("SELL", 0)
        nav.append(cash + sum(positions[s] * float(frames[s].iloc[t].close) for s in SYMBOLS))
    return pd.DataFrame(fills), np.array(nav), rejects


def main():
    prices = HERE / "input/btc_eth_daily.parquet"
    data = pd.read_parquet(prices)
    reports = []
    for case in ("ma60", "ema20", "williams14"):
        config = json.loads((HERE / f"input/ledgers/{case}.yaml").read_text())
        # 模拟阶段不读取成交账本、审计包或已有净值。
        fills, nav, rejects = simulate(data, config)
        actual = pd.read_parquet(HERE / f"input/ledgers/{case}.parquet")
        actual["timestamp"] = pd.to_datetime(actual.executed_at, utc=True)
        actual = actual.sort_values("timestamp", kind="stable").reset_index(drop=True)
        actual["day"] = actual.timestamp.dt.strftime("%Y-%m-%d")
        if len(actual) != len(fills):
            raise ValueError(f"{case}: 成交数不一致 {len(fills)} != {len(actual)}")
        for expected, observed in (("day", "day"), ("symbol", "symbol"), ("side", "order_type")):
            if fills[expected].tolist() != actual[observed].tolist():
                raise ValueError(f"{case}: {expected} 逐笔顺序不一致")
        diffs = {}
        for expected, observed in (("qty", "executed_qty"), ("price", "executed_price"),
                                   ("fee", "commission"), ("cash_after", "balance")):
            diffs[expected] = float(np.max(np.abs(fills[expected].to_numpy() - actual[observed].to_numpy())))
            if diffs[expected] > 1e-7:
                raise ValueError(f"{case}: {expected} 最大误差 {diffs[expected]}")
        package = json.loads((HERE / f"cases/{case}/audit_package.json").read_text(encoding="utf-8"))
        nav_diff = float(np.max(np.abs(nav - np.array([x["nav"] for x in package["daily_nav"]]))))
        if nav_diff > 1e-7 or rejects:
            raise ValueError(f"{case}: 净值或拒单不一致")
        report = dict(case=case, trades=len(fills), max_trade_errors=diffs,
                      max_daily_nav_error=nav_diff, rejects=rejects)
        reports.append(report)
        print(report)
    output = dict(
        method="从行情与配置独立计算信号及成交；模拟完成后才读取原账本比较",
        limitation="复现现有引擎规则，非独立样本外或策略有效性验证；不等同完整Go测试",
        reference_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        price_sha256=hashlib.sha256(prices.read_bytes()).hexdigest(), cases=reports)
    (HERE / "cases/independent_validation.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
