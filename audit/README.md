# 审计包（Audit Package）

## 它是什么

把一次回测的**全部可验证信息**打成一个规范化 JSON，只锚定它的 SHA-256：

```json
{
  "schema": "msbd5017.audit.v1",
  "experiment": { 策略、区间、币种、初始资金、费率、执行规则 },
  "code_commit": "23f1418",
  "data": { "btc_eth_daily.parquet": "sha256..." },
  "reference": { "reference_v2.py": "sha256..." },
  "trades": [ 168 笔逐笔成交（日期/币种/方向/数量/价格/费用/成交后现金）],
  "trades_merkle_root": "4ba9da5e...",
  "daily_nav": [ 每日净值 ],
  "nav_merkle_root": "af3489e8...",
  "summary": { "final_nav": 21428.07, "return_pct": 114.28 }
}
```

与组员原来的"单份结果 JSON"相比，审计包多了**逐笔成交、每日净值、数据与参考实现的哈希**，因此任何一笔成交被改动都会同时改变 Merkle root 和整包哈希。

## 生成

```bash
python audit/build_audit_package.py
```

产出：

- `audit_package.json` —— 审计包本体
- `audit_manifest.json` —— 包哈希与各 Merkle root 的清单

当前产物：

| 字段 | 值 |
|---|---|
| package_sha256 | `4c676f12fa0afe37342c7dd7d67d8b9724f8042b52db79b8e0a1c4756e07ea19` |
| trades_merkle_root | `4ba9da5e906820fef0b8fd30832a96f3ab2fbe31733ba9c25fc66dd3a14fcda9` |
| nav_merkle_root | `af3489e83f9f80f6af74019b5cc0e681eac64d2363a548206531212797347b59` |
| data_sha256 | `cbea5398f8947a3b4718029e44819828c7ac30e5919ae8373ebb2524cee1c610` |
| reference_sha256 | `3631f7fed5600a7138e8e309f6b9cb594c05be3862d0a6ce9cd04b6ed02dc08e` |

## 链下校验（不需要链）

```bash
python audit/verify_local.py
```

输出：

```
package sha256 : 4c676f12...
manifest sha256: 4c676f12...
match          : True
tampered sha256: a04714bb...
tamper detected: True
```

## 上链与读链验证

复用组员的 `BacktestRegistry` 合约（chainlab 测试网）：

```bash
# 1) 锚定审计包哈希
npx hardhat run scripts/anchor-audit.ts --network chainlab

# 2) 从链上读回并比对
npx hardhat run scripts/verify-audit.ts --network chainlab
```

锚定后会在 `audit/audit_package.proof.json` 生成凭据（record_id / tx hash / block number）。

## 篡改演示

1. 手动改 `audit_package.json` 里任意一笔 `qty` 或 `nav`；
2. 再跑 `verify-audit.ts`（或 `verify_local.py`），哈希不匹配 → **VERIFICATION FAILED**；
3. 改回原值 → 通过。

## 边界

链上只证明"这份审计包在某时刻被提交过、之后未被改"。它**不能**证明行情数据正确、策略有预测能力、或回测程序无 bug——后者由 `docs/迭代纪要/` 里的引擎审查与逐笔对账负责。
