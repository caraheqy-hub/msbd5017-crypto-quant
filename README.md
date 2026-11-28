# 加密策略研究工具：回测、分析与可验证记录

MSBD5017 · Group 27 · HE Qiyuan、ZHANG Xinyue

我们基于 Argo 做一个策略研究工具原型。研究者不仅要得到收益曲线，还要检查信号为何产生、交易如何执行、不同实验为什么有差异，并保存能交给别人核查的记录。

**回测记录上链与链上核验是我们项目的功能之一，由 ZHANG Xinyue 主导。** Hardhat 工程及本地验证已接入；三份审计包已在 chainlab 存证，文件指纹、网络、合约和交易凭据已核对，原包通过、修改副本失败、原包再次通过。实际记录与证据见 [测试网结果](docs/chainlab-results.md)。

MA60、EMA20、Williams14 是三个演示案例，用来检验同一研究流程能否支持不同规则。历史收益是案例输出，项目的目标是完善研究流程，并非推荐收益最高的策略。

## 从这里开始

| 想了解什么 | 阅读入口 |
|---|---|
| Argo 已有、需要修改、我们新增了什么（统一功能入口） | [项目功能清单](docs/项目功能清单.md) |
| 策略库、实验管理、AI 功能是否重复开发 | [专项源码核查](docs/策略库与实验管理_Argo重复功能核查.md) |
| 项目解决什么问题，当前做到了哪里 | [项目说明](项目说明.md) |
| Argo 提供什么、我们做了什么、还计划做什么 | [功能范围与开发计划](docs/功能范围与开发计划.md) |
| 官方 Argo 已有什么、修复依据与体验路线 | [Argo 功能盘点与体验指南](docs/Argo功能盘点与体验指南.md) |
| 两人的职责与 PR | [分工与验收](docs/分工与验收.md) |
| 同学可以接着做什么 | [给同学的任务说明](docs/给同学的任务说明.md) |
| 平台计算有哪些改进 | [平台改进说明](docs/平台改进说明.md) |
| 三案例的规则和结果 | [实验说明](final_project/README.md)、[结果表](final_project/cases/three_cases.md) |
| 中期两分钟 PPT 和讲稿 | [汇报材料](presentations/interim/README.md) |
| 审计包与历史记录 | [审计说明](audit/README.md)、[归档](archive/README.md) |

## 现在可以运行什么

在仓库根目录执行，需 Python 3.10 或以上：

```powershell
python -m pip install -r requirements.txt
python final_project/build_cases.py
python final_project/independent_replay.py
python audit/verify_local.py
python final_project/inspect_case.py --case ma60 --day 2022-03-02
python final_project/run_record.py record
```

`build_cases.py` 从三份保存的成交账本重建净值，检查账户计算，生成基准、市场状态、仓位和成本分析及 v2 审计包。`independent_replay.py` 从行情与配置独立重算三案例信号和成交，再与原账本对照。`verify_local.py` 针对原 MA60 v1 包演示本地哈希检查和篡改检测。`inspect_case.py` 按日期查看指标、信号、次日成交与账户变化；`run_record.py` 为每次实验生成带 `run_id` 的记录，并支持两次实验比较。

输出在 `final_project/cases/` 和 `final_project/runs/`。这套 Python 程序不是通用 Python 策略接入接口，也没有重新编译运行 Argo。当前已有命令行原型，交互式信号查看与实验管理页面尚未开发。

## 同学从这里开始

先运行上述命令，再读[任务说明](docs/给同学的任务说明.md)。你可以优先接入已有的 Hardhat 工程，并复核 Argo 修复版本；也可以与 Qiyuan 分担信号查看和实验记录功能。Qiyuan 负责研究需求、案例设计和功能验收，可参与平台代码与测试。两人共同确认优先级，避免同时开发多个策略入口。

## 目录

```text
docs/                   功能范围、分工、复核和交接
final_project/          演示案例、行情与成交、验证和分析脚本
audit/                  原 MA60 v1 审计包与历史生成脚本
scripts/                已接入 Hardhat 的本地与 chainlab 存证、验证脚本
presentations/interim/  当前两分钟汇报及讲稿
archive/                早期实验与讨论，不代表当前结论
```

已完成：三案例计算对照、账户检查、结果诊断脚本及审计包，Hardhat 接入和三案例 chainlab 存证核验。待完成：研究功能界面、实验记录完善、Argo 构建版本复核；存证工程已通过 [PR #1](https://github.com/caraheqy-hub/msbd5017-crypto-quant/pull/1) 合入主仓库；Qiyuan 跨电脑复查结果仍待确认。研究功能详见 [项目功能清单](docs/项目功能清单.md)，链上证据见 [测试网结果](docs/chainlab-results.md)。这个仓库是最终协作入口，旧 PPT 已归档。

## File format and reproducibility

Run `python scripts/check-reproducibility.py` to rebuild and compare two full runs.
See [format rules and version notes](docs/reproducibility.md) for the historical v1 exception and new v2 fingerprints.

## Local contract integration

The registry, parameterized audit tools and local tests are integrated.
Run `bun run build`, `bun run typecheck`, `bun run test`, then `bun run demo:local`.
The three-case demo uses an ephemeral local simulated chain; these are not testnet proofs.
See [local chain guide and source attribution](docs/chain-integration.md) and
[executed check results](docs/evidence/2026-11-20-chain-integration.json).

## Chainlab commands

See [step-by-step testnet commands](docs/chainlab-commands.md). Start with
`bun run chainlab:check` (read-only). Only `chainlab:anchor` sends a transaction.
Current package hashes and the existing registry are pinned in scripts/chainlab-manifest.json.

## Verified chainlab results

All three current audit packages have confirmed chainlab proofs. Original files
pass, modified copies fail, and originals pass again (9 independent CLI checks).
See [records, transactions and proof files](docs/chainlab-results.md).

## Demo and teammate handoff

See [beginner demonstration and handoff instructions](docs/演示与交接说明.md)
for read-only verification of all three cases, reproducible tampered copies,
contribution details and remaining work.

See [file-by-file changes and provenance](docs/文件改动清单.md) for the
imported contract, new code, teammate-code edits, generated results and format-only changes.
