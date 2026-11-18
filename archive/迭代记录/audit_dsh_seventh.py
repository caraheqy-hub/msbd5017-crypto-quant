"""Locate the first divergence between Argo MA60 and DSH's reference v2."""

import importlib.util
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


SOURCE = Path(r"D:\argo_work\btc\reference_v2.py")
spec = importlib.util.spec_from_file_location("reference_v2", SOURCE)
ref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref)

nav, fills, rejects, _, _ = ref.run()
actual = pq.read_table(ref.RUN / "state.db/trades.parquet").to_pandas()
actual["day"] = pd.to_datetime(actual.executed_at).dt.date.astype(str)
reference = pd.DataFrame(fills, columns=["day", "symbol", "side", "ref_qty", "ref_price", "ref_fee", "ref_cash"])
assert len(actual) == len(reference) == 168
key = actual[["day", "symbol", "order_type"]].copy()
key.columns = ["day", "symbol", "side"]
assert key.reset_index(drop=True).equals(reference[["day", "symbol", "side"]].reset_index(drop=True))
comparison = pd.concat([actual[["day", "symbol", "order_type", "executed_qty", "executed_price", "commission", "balance"]].reset_index(drop=True), reference[["ref_qty", "ref_price", "ref_fee", "ref_cash"]]], axis=1)
comparison["qty_diff"] = comparison.executed_qty - comparison.ref_qty
comparison["cash_diff"] = comparison.balance - comparison.ref_cash
print("first quantity mismatch:")
first = comparison.index[comparison.qty_diff.abs() > 1e-8][0]
print(comparison.iloc[max(0, first-4):first+5].to_string(index=True))
print("qty unique differences", sorted(comparison.qty_diff.round(4).unique()))
print("cash difference before first", comparison.iloc[first-1].cash_diff)
print("cash difference at first", comparison.iloc[first].cash_diff)

# Check the reference's claim that quantity is unchanged by fee or slippage.
for label, kwargs in [("fee20", {"fee": 0.002}), ("fee40", {"fee": 0.004}),
                      ("slip10", {"slip": 0.001}), ("slip20", {"slip": 0.002}),
                      ("slip50", {"slip": 0.005})]:
    _, other_fills, other_rejects, _, _ = ref.run(**kwargs)
    changes = sum(a[3] != b[3] for a, b in zip(fills, other_fills))
    print(label, "fills", len(other_fills), "qty_changes", changes,
          "rejects", other_rejects, "same_order_keys", [x[:3] for x in fills] == [x[:3] for x in other_fills])

# The Go engine exposes a fee-adjusted maximum buy quantity. Test whether
# applying the fee in the sizing denominator resolves the first mismatch.
source = SOURCE.read_text(encoding="utf-8")
old = "np.floor(cash * DEPLOY / cl * 100) / 100"
new = "np.floor(cash * DEPLOY / (cl * (1 + fee)) * 100) / 100"
assert old in source
scope = {"__name__": "ref_hypothesis"}
exec(compile(source.replace(old, new), str(SOURCE), "exec"), scope)
_, adjusted_fills, _, _, _ = scope["run"]()
adjusted = pd.DataFrame(adjusted_fills, columns=reference.columns)
adjusted_diff = actual.executed_qty.reset_index(drop=True) - adjusted.ref_qty
print("fee-adjusted sizing", {
    "quantity_mismatches": int((adjusted_diff.abs() > 1e-8).sum()),
    "first_mismatch": int(adjusted_diff.index[adjusted_diff.abs() > 1e-8][0]),
    "max_abs_qty_error": float(adjusted_diff.abs().max()),
})
print("first adjusted mismatch rows:")
ix = adjusted_diff.index[adjusted_diff.abs() > 1e-8][0]
print(pd.concat([actual[["day", "symbol", "order_type", "executed_qty", "balance"]].reset_index(drop=True),
                 adjusted[["ref_qty", "ref_cash"]]], axis=1).iloc[ix-2:ix+3].to_string(index=True))
