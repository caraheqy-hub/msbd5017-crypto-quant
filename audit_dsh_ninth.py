"""Reconcile DSH's corrected MA60 run to the reference model."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


source = Path(r"D:\argo_work\btc\reference_v2.py")
spec = importlib.util.spec_from_file_location("dsh_reference_v2", source)
ref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref)
ref.RUN = Path(r"D:\argo_work\btc\results_utilfix\20261118_234959\Search\03_ma60\btc_eth_daily")

nav, fills, rejects, cash, positions = ref.run()
actual, actual_nav = ref.argo_nav()
orders = pq.read_table(ref.RUN / "state.db/orders.parquet").to_pandas()
reference = pd.DataFrame(fills, columns=["day", "symbol", "side", "qty", "price", "fee", "cash"])
actual_keys = actual[["day", "symbol", "order_type"]].reset_index(drop=True)
actual_keys.columns = ["day", "symbol", "side"]
keys_equal = actual_keys.equals(reference[["day", "symbol", "side"]].reset_index(drop=True))
assert len(actual) == len(reference) == len(orders) == 168 and keys_equal

def maxdiff(a, b):
    return float(np.max(np.abs(np.asarray(a) - np.asarray(b))))

print({
    "trades": len(actual), "orders": len(orders), "statuses": orders.status.value_counts().to_dict(),
    "keys_equal": keys_equal, "price_error": maxdiff(actual.executed_price, reference.price),
    "quantity_error": maxdiff(actual.executed_qty, reference.qty),
    "fee_error": maxdiff(actual.commission, reference.fee),
    "cash_error": maxdiff(actual.balance, reference.cash),
    "nav_error": maxdiff(actual_nav, nav), "final_argo_nav": float(actual_nav[-1]),
    "final_reference_nav": float(nav[-1]), "return": float(actual_nav[-1] / actual_nav[0] - 1),
    "daily_sharpe": float(ref.metrics(actual_nav)["sharpe"]),
    "mdd": float(ref.metrics(actual_nav)["mdd"]),
    "min_cash": float(actual.balance.min()), "rejects": rejects,
})

for label, kwargs in [("fee20", {"fee": 0.002}), ("fee40", {"fee": 0.004}),
                      ("slip10", {"slip": 0.001}), ("slip20", {"slip": 0.002}),
                      ("slip50", {"slip": 0.005})]:
    scenario_nav, scenario_fills, scenario_rejects, _, _ = ref.run(**kwargs)
    print(label, {
        "return": float(ref.metrics(scenario_nav)["ret"]),
        "qty_changes": sum(a[3] != b[3] for a, b in zip(fills, scenario_fills)),
        "same_keys": [x[:3] for x in fills] == [x[:3] for x in scenario_fills],
        "rejects": scenario_rejects,
    })
