"""Reproducible BTC/ETH spot backtest with a verifiable artifact root."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ASSETS = ("BTCUSDT", "ETHUSDT")
FEE = 0.001
CONFIG = {"assets": ASSETS, "fee_per_turnover": FEE, "trend_windows": [20, 60],
          "reversal_days": 5, "regime_days": 30, "regime_threshold": 0.10,
          "holdout_fraction": 0.30, "fill": "next daily close after signal"}


def canonical(obj):
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def generate_demo(path):
    rng = random.Random(5017)
    p = [17000.0, 1200.0]
    start = date(2023, 1, 1)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["date", "symbol", "close"])
        for day in range(720):
            regime = (day // 120) % 3
            drift = [0.003, -0.0025, 0.0001][regime]
            common = rng.gauss(0, 0.025)
            for j, symbol in enumerate(ASSETS):
                p[j] *= math.exp(drift * (1.25 if j else 1) + common * (1.2 if j else 1) + rng.gauss(0, 0.008))
                w.writerow([(start + timedelta(days=day)).isoformat(), symbol, f"{p[j]:.8f}"])


def fetch(start, end, path):
    if end <= start:
        raise ValueError("end must be after start")
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for symbol in ASSETS:
        cursor = int(datetime.combine(start, datetime.min.time(), timezone.utc).timestamp() * 1000)
        finish = int(datetime.combine(end, datetime.min.time(), timezone.utc).timestamp() * 1000)
        while cursor < finish:
            query = urllib.parse.urlencode({"symbol": symbol, "interval": "1d", "startTime": cursor,
                                             "endTime": finish - 1, "limit": 1000})
            url = "https://data-api.binance.vision/api/v3/klines?" + query
            with urllib.request.urlopen(url, timeout=20) as response:
                batch = json.load(response)
            if not batch:
                break
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
            for bar in batch:
                if int(bar[6]) < now_ms:
                    rows.append((datetime.fromtimestamp(bar[0] / 1000, timezone.utc).date().isoformat(), symbol, bar[4]))
            next_cursor = int(batch[-1][0]) + 86_400_000
            if next_cursor <= cursor:
                raise RuntimeError("Binance pagination did not advance")
            cursor = next_cursor
    rows.sort()
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["date", "symbol", "close"])
        w.writerows(rows)
    return len(rows)


def read_prices(path):
    by_day = {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not {"date", "symbol", "close"}.issubset(reader.fieldnames or []):
            raise ValueError("CSV requires date,symbol,close")
        for row in reader:
            d = date.fromisoformat(row["date"])
            symbol = row["symbol"]
            if symbol not in ASSETS:
                continue
            value = float(row["close"])
            if not math.isfinite(value) or value <= 0:
                raise ValueError("close must be finite and positive")
            if symbol in by_day.setdefault(d, {}):
                raise ValueError(f"duplicate {d} {symbol}")
            by_day[d][symbol] = value
    dates = sorted(by_day)
    if len(dates) < 120 or any(set(by_day[d]) != set(ASSETS) for d in dates):
        raise ValueError("need >=120 aligned dates for BTCUSDT and ETHUSDT")
    if any((dates[i] - dates[i-1]).days != 1 for i in range(1, len(dates))):
        raise ValueError("daily dates must be consecutive; inspect missing candles")
    return dates, [[by_day[d][a] for a in ASSETS] for d in dates]


def weights(strategy, prices, signal_idx):
    if strategy == "btc_hold":
        return [1.0, 0.0]
    if strategy == "equal_weight":
        return [0.5, 0.5]
    if strategy == "trend":
        return [0.5 if sum(row[j] for row in prices[signal_idx-19:signal_idx+1]) / 20 >
                sum(row[j] for row in prices[signal_idx-59:signal_idx+1]) / 60 else 0.0 for j in range(2)]
    if strategy == "reversal":
        rets = [prices[signal_idx][j] / prices[signal_idx-5][j] - 1 for j in range(2)]
        return [1.0, 0.0] if rets[0] < rets[1] else [0.0, 1.0]
    a, b = weights("trend", prices, signal_idx), weights("reversal", prices, signal_idx)
    return [(a[j] + b[j]) / 2 for j in range(2)]


def metrics(returns):
    if not returns:
        return {"days": 0, "total_return": None, "volatility": None, "sharpe": None, "max_drawdown": None}
    mean = sum(returns) / len(returns)
    std = math.sqrt(sum((r-mean)**2 for r in returns) / (len(returns)-1)) if len(returns) > 1 else 0
    equity = peak = 1.0
    mdd = 0.0
    for r in returns:
        equity *= 1+r
        peak = max(peak, equity)
        mdd = min(mdd, equity/peak-1)
    return {"days": len(returns), "total_return": round(equity-1, 6),
            "volatility": round(std*math.sqrt(365), 6),
            "sharpe": round(mean/std*math.sqrt(365), 6) if std else None,
            "max_drawdown": round(mdd, 6)}


def backtest(dates, prices):
    names = ("btc_hold", "equal_weight", "trend", "reversal", "blend")
    first, last = 60, len(prices)-1
    cutoff = first + int((last-first)*0.70)
    prev = {name: [0.0, 0.0] for name in names}
    trades = []
    daily = {name: [] for name in names}
    for i in range(first, last):
        signal_idx = i-1
        thirty = prices[signal_idx][0] / prices[signal_idx-30][0]-1
        regime = "bull" if thirty > 0.10 else "bear" if thirty < -0.10 else "sideways"
        period = "development" if i < cutoff else "holdout"
        asset_return = [prices[i+1][j]/prices[i][j]-1 for j in range(2)]
        for name in names:
            target = weights(name, prices, signal_idx)
            turnover = sum(abs(target[j]-prev[name][j]) for j in range(2))
            fee = FEE*turnover
            net = sum(target[j]*asset_return[j] for j in range(2))-fee
            if net <= -1:
                raise ValueError("return below -100%")
            daily[name].append({"date": dates[i+1].isoformat(), "period": period,
                                "regime": regime, "return": round(net, 10)})
            if turnover:
                trades.append({"strategy": name, "signal_date": dates[signal_idx].isoformat(),
                               "execution_date": dates[i].isoformat(), "weights": target,
                               "turnover": round(turnover, 6), "fee_fraction": round(fee, 8)})
            gross = 1 + sum(target[j]*asset_return[j] for j in range(2))
            prev[name] = [target[j]*(1+asset_return[j])/gross for j in range(2)]
    summary = {}
    for name in names:
        summary[name] = {}
        for period in ("development", "holdout"):
            subset = [r for r in daily[name] if r["period"] == period]
            summary[name][period] = metrics([r["return"] for r in subset])
            summary[name][period]["regimes"] = {
                regime: {"days": len(v), "mean_daily_return": round(sum(v)/len(v), 8) if v else None}
                for regime in ("bull", "bear", "sideways")
                for v in [[r["return"] for r in subset if r["regime"] == regime]]}
    return trades, daily, summary


def run(csv_path, out, synthetic=False):
    dates, prices = read_prices(csv_path)
    trades, daily, summary = backtest(dates, prices)
    out.mkdir(parents=True, exist_ok=True)
    (out/"trades.json").write_bytes(canonical(trades))
    (out/"daily.json").write_bytes(canonical(daily))
    (out/"summary.json").write_bytes(canonical(summary))
    (out/"prices.csv").write_bytes(csv_path.read_bytes())
    inputs = {name: digest((out/name).read_bytes()) for name in ("prices.csv", "trades.json", "daily.json", "summary.json")}
    inputs["backtest.py"] = digest(Path(__file__).read_bytes())
    manifest = {"version": 1, "synthetic_data": synthetic, "config": CONFIG,
                "first_date": dates[0].isoformat(), "last_date": dates[-1].isoformat(), "sha256": inputs}
    root = digest(canonical(manifest))
    (out/"audit.json").write_bytes(canonical({"manifest": manifest, "root": root}))
    print(json.dumps({"root": root, "synthetic_data": synthetic, "summary": summary}, indent=2))


def verify(out):
    record = json.loads((out/"audit.json").read_bytes())
    manifest = record["manifest"]
    for name, expected in manifest["sha256"].items():
        path = Path(__file__) if name == "backtest.py" else out/name
        if digest(path.read_bytes()) != expected:
            raise ValueError(f"digest mismatch: {name}")
    if digest(canonical(manifest)) != record["root"]:
        raise ValueError("root mismatch")
    print("Verified artifact root:", record["root"])


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("demo").add_argument("--out", type=Path, required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--start", type=date.fromisoformat, required=True)
    f.add_argument("--end", type=date.fromisoformat, required=True, help="exclusive UTC end date")
    f.add_argument("--out", type=Path, required=True)
    r = sub.add_parser("run")
    r.add_argument("--csv", type=Path, required=True)
    r.add_argument("--out", type=Path, required=True)
    sub.add_parser("verify").add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if args.command == "demo":
        args.out.mkdir(parents=True, exist_ok=True)
        path = args.out/"synthetic_prices.csv"
        generate_demo(path)
        run(path, args.out, synthetic=True)
    elif args.command == "fetch":
        print("Downloaded rows:", fetch(args.start, args.end, args.out))
    elif args.command == "run":
        run(args.csv, args.out)
    else:
        verify(args.out)


if __name__ == "__main__":
    main()
