# 审计包怎么检查

这里保存最初 MA60 的 v1 包，作为历史核对基准。三个候选策略的新 v2 包位于 `final_project/cases/`，用根目录命令 `python final_project/build_cases.py` 重建。新包补入了指标配置和来源指纹，整包哈希有变化。三个已确认的 v2 包已在 chainlab 存证，记录为 9、10、11，凭据位于 `../proofs/chainlab/`，见 [测试网结果](../docs/chainlab-results.md)。此处历史 v1 包与三份 v2 包不能混用凭据。

`audit_package.json` 保存这次 MA60 回测的参数、数据和代码指纹、168 笔成交，以及 1765 天账户净值。`audit_manifest.json` 保存该文件的 SHA-256 和两棵 Merkle 树的根哈希。Merkle 树是对多条记录逐层计算指纹的方法，便于检查记录是否一致。

当前包的 SHA-256 是：

```text
4c676f12fa0afe37342c7dd7d67d8b9724f8042b52db79b8e0a1c4756e07ea19
```

## 本地能做的检查

在仓库根目录运行：

```powershell
python audit/verify_local.py
```

脚本比较包与本地清单的哈希，然后在内存中改一笔数量，演示哈希变化。不会修改原文件。这个检查只能说明文件与本地清单一致；若包和清单一起被替换，本地比较无法提供外部证明。

## 仍需完成的部分

`build_audit_package.py` 是原生成脚本，仍使用作者电脑的绝对路径；新电脑上暂时不能直接生成同一份包。PR 2 要补齐可移植的生成过程、输入检查、Merkle 重算和账本复核。原始参考代码位于 `../final_project/input/reference_v2.py`，改动后代码哈希会变化，需记录新旧包的版本关系。

Hardhat 工程、合约和网络配置已接入。`../scripts/anchor-audit.ts` 与 `verify-audit.ts` 是本地链入口；chainlab 使用 `anchor-chainlab.ts` 与 `verify-chainlab.ts`。审核三份已存证 v2 包时，选择对应 `AUDIT_CASE` 并运行 `bun run chainlab:verify`；无需解锁账户或重新发交易。

三份 v2 包已完成：提交文件哈希 → 保存交易凭据 → 从链上读回哈希 → 原文件验证通过 → 修改副本验证失败 → 原文件再次通过。本目录历史 v1 审计包没有在本项目保存对应的真实链上凭据，不能用 v2 记录代替它，也不应将此 v1 包写为“已上链”。执行者在本机配置账户，无需向组员发送私钥。

区块链能提供外部的提交记录；程序是否正确仍需测试和对账，策略是否有效仍需研究。
