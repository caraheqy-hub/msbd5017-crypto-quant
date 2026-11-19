"""按日期查看某案例的指标、信号、次日成交与账户变化。

运行：
    python final_project/inspect.py --case ma60 --day 2023-01-15
    python final_project/inspect.py --case ema20 --day 2023-01-15
    python final_project/inspect.py --case williams14 --day 2023-01-15
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from independent_replay import indicator_values, SYMBOLS

HERE = Path(__file__).resolve().parent


def load_case(case: str):
    config = json.loads((HERE / f"input/ledgers/{case}.yaml").read_text())
    data = pd.read_parquet(HERE / "input/btc_eth_daily.parquet")
    frames = {
        s: data[data.symbol == s].sort_values("time").reset_index(drop=True)
        for s in SYMBOLS
    }
    values = {s: indicator_values(frames[s], config["kind"], config["period"]) for s in SYMBOLS}
    fills = pd.read_parquet(HERE / f"input/ledgers/{case}.parquet")
    fills["timestamp"] = pd.to_datetime(fills.executed_at, utc=True)
    fills = fills.sort_values("timestamp", kind="stable").reset_index(drop=True)
    fills["day"] = fills.timestamp.dt.strftime("%Y-%m-%d")
    return config, frames, values, fills


def position_after(fills: pd.DataFrame, symbol: str, day: str) -> float:
    """收盘时持仓：当日成交已计入，因为信号是收盘后用这个持仓判断的。"""
    prior = fills[(fills.symbol == symbol) & (fills.day <= day)]
    buy = prior[prior.order_type == "BUY"].executed_qty.sum()
    sell = prior[prior.order_type == "SELL"].executed_qty.sum()
    return float(buy - sell)


def inspect(case: str, day: str) -> dict:
    config, frames, values, fills = load_case(case)
    dates = frames[SYMBOLS[0]].time.dt.strftime("%Y-%m-%d").tolist()
    if day not in dates:
        raise SystemExit(f"{day} 不在数据区间（{dates[0]} ~ {dates[-1]}）")
    t = dates.index(day)
    next_day = dates[t + 1] if t + 1 < len(dates) else None

    kind = config["kind"]
    period = config["period"]
    out = {"case": case, "day": day, "kind": kind, "period": period, "symbols": {}}

    for symbol in SYMBOLS:
        bar = frames[symbol].iloc[t]
        close = float(bar.close)
        value = float(values[symbol][t]) if not np.isnan(values[symbol][t]) else None
        pos = position_after(fills, symbol, day)

        if value is None:
            signal, reason = "预热不足", f"历史不足 {period} 根，指标无法计算"
        elif kind == "williams":
            if value < config["oversold"]:
                signal, reason = "买入", f"%R={value:.2f} < 超卖阈值 {config['oversold']}"
            elif value > config["overbought"]:
                signal, reason = "卖出", f"%R={value:.2f} > 超买阈值 {config['overbought']}"
            else:
                signal, reason = "无动作", f"%R={value:.2f} 在 [{config['oversold']}, {config['overbought']}] 之间"
        else:
            label = "MA" if kind == "ma" else "EMA"
            if close > value:
                signal, reason = "买入", f"收盘 {close:.2f} > {label}{period} {value:.2f}"
            elif close < value:
                signal, reason = "卖出", f"收盘 {close:.2f} < {label}{period} {value:.2f}"
            else:
                signal, reason = "无动作", f"收盘 {close:.2f} = {label}{period} {value:.2f}"

        if signal == "买入" and pos > 0:
            signal, reason = "无动作", reason + "；已持仓，不重复买入"
        if signal == "卖出" and pos <= 0:
            signal, reason = "无动作", reason + "；空仓，无可卖"

        fill = None
        if next_day:
            nxt = fills[(fills.day == next_day) & (fills.symbol == symbol)]
            if len(nxt):
                row = nxt.iloc[0]
                fill = {
                    "day": next_day,
                    "side": row.order_type,
                    "qty": float(row.executed_qty),
                    "price": float(row.executed_price),
                    "fee": float(row.commission),
                    "cash_after": float(row.balance),
                }

        warmup = None
        if kind == "ema":
            bars = t + 1
            warmup = {
                "bars": bars,
                "mode": "SMA fallback" if bars < period * 3 else "EMA recursion from period",
                "note": "不足 3 倍周期时退回最近 period 根的简单均值，满后从 period 根初始化并递推",
            }

        out["symbols"][symbol] = {
            "close": close,
            "indicator": value,
            "position": pos,
            "signal": signal,
            "reason": reason,
            "next_day_fill": fill,
            "ema_warmup": warmup,
        }

    return out


def render(report: dict) -> str:
    lines = [f"案例 {report['case']}  日期 {report['day']}  指标 {report['kind']}{report['period']}"]
    for symbol, row in report["symbols"].items():
        value = "n/a" if row["indicator"] is None else f"{row['indicator']:.2f}"
        lines.append("")
        lines.append(f"{symbol}: 收盘 {row['close']:.2f}  指标 {value}  持仓 {row['position']:.2f}")
        lines.append(f"  信号: {row['signal']} —— {row['reason']}")
        if row["ema_warmup"]:
            w = row["ema_warmup"]
            lines.append(f"  EMA 预热: {w['bars']} 根（{w['mode']}）")
        if row["next_day_fill"]:
            f = row["next_day_fill"]
            lines.append(
                f"  次日 {f['day']} 成交: {f['side']} {f['qty']:.2f} @ {f['price']:.2f}，"
                f"费 {f['fee']:.2f}，成交后现金 {f['cash_after']:.2f}"
            )
        else:
            lines.append("  次日无成交")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True, choices=["ma60", "ema20", "williams14"])
    parser.add_argument("--day", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = inspect(args.case, args.day)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render(report))
