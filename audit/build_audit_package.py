"""Build the audit package for the MA60 shared-account experiment.

The package is a single canonical JSON whose SHA-256 is what gets anchored.
It contains the full trade ledger and daily NAV, plus their Merkle roots, so
editing any single trade changes both the root and the package hash.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

REF = Path(r"D:\argo_work\btc\reference_v2.py")
OUT = Path(r"D:\argo_work\group27_trade\audit")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def leaf(obj) -> str:
    canon = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_hex(canon.encode("utf-8"))


def merkle_root(leaves: list[str]) -> str:
    if not leaves:
        return sha256_hex(b"")
    level = [bytes.fromhex(h) for h in leaves]
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [hashlib.sha256(a + b).digest() for a, b in zip(level[::2], level[1::2])]
    return level[0].hex()


def main() -> None:
    spec = importlib.util.spec_from_file_location("ref", REF)
    ref = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ref)

    nav, fills, rejects, cash, pos = ref.run()

    data_path = ref.DATA
    data_sha = sha256_hex(Path(data_path).read_bytes())
    ref_sha = sha256_hex(REF.read_bytes())

    trades = [
        {
            "day": day,
            "symbol": symbol,
            "side": side,
            "qty": round(qty, 10),
            "price": round(price, 10),
            "fee": round(fee, 10),
            "cash_after": round(cash_after, 10),
        }
        for day, symbol, side, qty, price, fee, cash_after in fills
    ]
    trade_leaves = [leaf(t) for t in trades]

    days = [str(pd_ts.date()) for pd_ts in ref.btc.time]
    daily_nav = [{"day": d, "nav": round(float(v), 10)} for d, v in zip(days, nav)]
    nav_leaves = [leaf(x) for x in daily_nav]

    package = {
        "schema": "msbd5017.audit.v1",
        "experiment": {
            "name": "ma60_shared_account_btc_eth",
            "strategy": "MA60 trend (close>MA60 buy, close<MA60 sell)",
            "period": {"start": days[0], "end": days[-1]},
            "symbols": ["BTCUSDT", "ETHUSDT"],
            "initial_capital": 10000.0,
            "deploy_fraction": 0.45,
            "fee_per_side": 0.001,
            "execution": "signal at bar t close, fill at bar t+1 open",
            "portfolio": "single shared cash account",
        },
        "code_commit": "23f1418",
        "engine": "argo-trading (fix/quantity-float-precision)",
        "data": {
            "path": Path(data_path).name,
            "sha256": data_sha,
        },
        "reference": {
            "path": REF.name,
            "sha256": ref_sha,
        },
        "summary": {
            "trades": len(trades),
            "rejects": rejects,
            "final_cash": round(cash, 4),
            "final_nav": round(float(nav[-1]), 4),
            "return_pct": round(float(nav[-1] / nav[0] - 1) * 100, 4),
        },
        "trades": trades,
        "trades_merkle_root": merkle_root(trade_leaves),
        "daily_nav": daily_nav,
        "nav_merkle_root": merkle_root(nav_leaves),
    }

    text = json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    OUT.mkdir(parents=True, exist_ok=True)

    pkg_path = OUT / "audit_package.json"
    pkg_path.write_text(text, encoding="utf-8")
    pkg_sha = sha256_hex(pkg_path.read_bytes())

    manifest = {
        "package": pkg_path.name,
        "package_sha256": pkg_sha,
        "trades_merkle_root": package["trades_merkle_root"],
        "nav_merkle_root": package["nav_merkle_root"],
        "data_sha256": data_sha,
        "reference_sha256": ref_sha,
        "code_commit": package["code_commit"],
    }
    (OUT / "audit_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"package: {pkg_path}")


if __name__ == "__main__":
    main()
