"""Read-only, independent checks of Group 27's proposed audit package."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


AUDIT = Path(r"D:\argo_work\group27_trade\audit")
TRADES = Path(r"D:\argo_work\btc\results_utilfix\20261118_234959\Search\03_ma60\btc_eth_daily\state.db\trades.parquet")
package_bytes = (AUDIT / "audit_package.json").read_bytes()
package = json.loads(package_bytes)
manifest = json.loads((AUDIT / "audit_manifest.json").read_text(encoding="utf-8"))


def digest(data):
    return hashlib.sha256(data).digest()


def root(items):
    leaves = [digest(json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")) for x in items]
    if not leaves:
        return digest(b"").hex()
    while len(leaves) > 1:
        if len(leaves) % 2:
            leaves.append(leaves[-1])
        leaves = [digest(a + b) for a, b in zip(leaves[::2], leaves[1::2])]
    return leaves[0].hex()


trades = pq.read_table(TRADES).to_pandas()
pkg_trades = pd.DataFrame(package["trades"])
trades["day"] = pd.to_datetime(trades.executed_at).dt.date.astype(str)
keys = trades[["day", "symbol", "order_type"]].reset_index(drop=True)
keys.columns = ["day", "symbol", "side"]
pkg_keys = pkg_trades[["day", "symbol", "side"]].reset_index(drop=True)
assert len(trades) == len(pkg_trades) == 168 and keys.equals(pkg_keys)

print({
    "package_hash_matches_manifest": digest(package_bytes).hex() == manifest["package_sha256"],
    "trades_root_matches": root(package["trades"]) == package["trades_merkle_root"] == manifest["trades_merkle_root"],
    "nav_root_matches": root(package["daily_nav"]) == package["nav_merkle_root"] == manifest["nav_merkle_root"],
    "trades": len(pkg_trades), "nav_days": len(package["daily_nav"]),
    "trade_keys_match_argo": True,
    "max_price_error": float(np.max(np.abs(trades.executed_price - pkg_trades.price))),
    "max_qty_error": float(np.max(np.abs(trades.executed_qty - pkg_trades.qty))),
    "max_fee_error": float(np.max(np.abs(trades.commission - pkg_trades.fee))),
    "max_cash_error": float(np.max(np.abs(trades.balance - pkg_trades.cash_after))),
})
