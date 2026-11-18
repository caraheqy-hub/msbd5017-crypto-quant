"""从仓库内成交账本重建三案例，并运行相同的基准和状态分析。"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
INPUT = HERE / "input"
OUT = HERE / "cases"
CASES = [("ma60", "MA60 简单均线"), ("ema20", "EMA20 指数均线"),
         ("williams14", "Williams %R 14")]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def merkle(items):
    level = [hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).digest() for x in items]
    if not level:
        return hashlib.sha256(b"").hexdigest()
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [hashlib.sha256(a + b).digest() for a, b in zip(level[::2], level[1::2])]
    return level[0].hex()


def build(name, label):
    prices = INPUT / "btc_eth_daily.parquet"
    ledger = INPUT / "ledgers" / f"{name}.parquet"
    config = INPUT / "ledgers" / f"{name}.yaml"
    data = pd.read_parquet(prices)
    close = data.pivot(index="time", columns="symbol", values="close").sort_index()
    opens = data.pivot(index="time", columns="symbol", values="open").sort_index()
    tr = pd.read_parquet(ledger)
    tr["timestamp"] = pd.to_datetime(tr.executed_at, utc=True)
    # 同时刻必须保留原始行顺序，balance 是逐笔成交后现金。
    tr = tr.sort_values("timestamp", kind="stable")
    tr["day"] = tr.timestamp.dt.strftime("%Y-%m-%d")
    days = set(pd.to_datetime(close.index, utc=True).strftime("%Y-%m-%d"))
    if not set(tr.day).issubset(days):
        raise ValueError("成交日期不在价格区间内")
    positions = dict.fromkeys(close.columns, 0.0)
    cash, entries, nav = 10000.0, [], []
    max_cash_error = 0.0
    for time, row in close.iterrows():
        day = time.strftime("%Y-%m-%d")
        for _, trade in tr[tr.day == day].iterrows():
            side, symbol = trade.order_type, trade.symbol
            if side not in ("BUY", "SELL") or symbol not in positions:
                raise ValueError("未知方向或币种")
            qty, price, fee = map(float, [trade.executed_qty, trade.executed_price, trade.commission])
            if qty <= 0 or abs(price - float(opens.loc[time, symbol])) > 1e-8:
                raise ValueError("成交数量非法或成交价不等于当日开盘价")
            if abs(fee - qty * price * .001) > 1e-6:
                raise ValueError("手续费与10bp规则不符")
            sign = 1 if side == "BUY" else -1
            cash -= sign * qty * price + fee
            positions[symbol] += sign * qty
            error = abs(cash - float(trade.balance))
            max_cash_error = max(max_cash_error, error)
            if error > 1e-6 or cash < -1e-6 or min(positions.values()) < -1e-8:
                raise ValueError(f"{name} {day} 余额或持仓校验失败")
            entries.append(dict(day=day, symbol=symbol, side=side,
                                qty=round(qty, 10), price=round(price, 10),
                                fee=round(fee, 10), cash_after=round(cash, 10)))
        nav.append(dict(day=day, nav=round(cash + sum(positions[s] * float(row[s])
                                                    for s in positions), 10)))
    if len(entries) != len(tr):
        raise ValueError("成交记录未全部重放")
    package = {
        "schema": "msbd5017.audit.v2",
        "experiment": dict(name=name, strategy=label,
                           indicator_config=json.loads(config.read_text()),
                           period=dict(start=nav[0]["day"], end=nav[-1]["day"]),
                           symbols=list(positions), initial_capital=10000.0,
                           deploy_fraction=.45, quantity_decimal_places=2, fee_per_side=.001,
                           execution="signal at bar t close, fill at bar t+1 open",
                           portfolio="single shared cash account"),
        "data": dict(path=prices.name, sha256=sha(prices)),
        "provenance": {
            "source_run": "results_utilfix/20261118_234959/Search",
            "engine_commit_reported": "23f1418",
            "engine_commit_status": "历史记录所报版本；尚未在本仓库从该提交重跑引擎",
            "ledger_sha256": sha(ledger), "indicator_config_sha256": sha(config),
            "strategy_source_sha256": sha(INPUT / "ledgers/strategy_search.go"),
            "engine_config_sha256": sha(INPUT / "ledgers/engine_config.yaml"),
            "builder_sha256": sha(Path(__file__)),
            "validation": "账本现金、持仓、费用及开盘价检查；不等于独立重算指标信号",
        },
        "trades": entries, "daily_nav": nav,
        "trades_merkle_root": merkle(entries), "nav_merkle_root": merkle(nav),
    }
    out = OUT / name
    out.mkdir(parents=True, exist_ok=True)
    pkg = out / "audit_package.json"
    pkg.write_text(json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    values = np.array([x["nav"] for x in nav])
    summary = dict(case=name, label=label, **{"return": values[-1] / 10000 - 1},
                   mdd=float(min(values / np.maximum.accumulate(values) - 1)),
                   trades=len(entries), final_nav=float(values[-1]),
                   package_sha256=sha(pkg), trades_merkle_root=merkle(entries),
                   nav_merkle_root=merkle(nav), max_cash_error=max_cash_error)
    (out / "case_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{name}: {len(entries)} 笔；逐笔现金最大差 {max_cash_error:.3g}", flush=True)
    return pkg, out


if __name__ == "__main__":
    for name, label in CASES:
        package, out = build(name, label)
        subprocess.run([sys.executable, str(HERE / "regime_analysis.py"),
                        "--prices", str(INPUT / "btc_eth_daily.parquet"),
                        "--audit-package", str(package), "--output-dir", str(out)],
                       check=True, stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable, str(OUT / "summarize_cases.py")], check=True)
