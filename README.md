# BTC/ETH 策略回测与链上存证

MSBD5017 · Group 27 · HE Qiyuan、ZHANG Xinyue

我们比较三个候选策略：MA60 简单均线、EMA20 指数均线和 Williams14 区间位置信号。它们分别决定何时持有 BTC 和 ETH，再与一直持有比较。我们同时检查回测程序，把交易和每日账户净值整理成审计包，准备将文件指纹写到区块链上。

## 从哪里开始看

| 你想了解什么 | 看这里 |
|---|---|
| 项目为什么做、目前做到了哪里 | [项目说明](项目说明.md) |
| 两个人各做什么、下一步怎么提 PR | [分工与验收](docs/分工与验收.md) |
| 同学现在可以接着做什么 | [给 Xinyue 的任务说明](docs/给同学的任务说明.md) |
| 我们对 Argo 改了什么、还建议改什么 | [平台改进说明](docs/平台改进说明.md) |
| 当前回测的规则和结果怎么理解 | [实验方法与结果](final_project/README.md) |
| 三个策略比基准多赚多少 | [三案例结果表](final_project/cases/three_cases.md) |
| 审计包是什么、怎样检查 | [审计包说明](audit/README.md) |
| 以前讨论过什么、数字为什么变过 | [历史材料](archive/README.md)；这些不是当前结论 |

## 先运行已有的分析

在仓库根目录执行，需要 Python 3.10 或以上：

```powershell
python -m pip install -r requirements.txt
python final_project/build_cases.py
python final_project/independent_replay.py
python audit/verify_local.py
```

第一条命令重放仓库内三份成交账本，核对现金、开盘价和费用，重建净值，再计算基准及市场状态分析。输出在 `final_project/cases/`；它没有重新运行 Argo 的信号生成过程。第二条命令检查原 MA60 v1 包的本地哈希，并演示改动检测。

## 仓库结构

```text
README.md               阅读入口和运行命令
项目说明.md              项目目标、现状和交付内容
docs/                   分工、PR 和验收要求
final_project/          当前实验的数据、分析脚本和结果
audit/                  当前审计包及检查脚本
scripts/                待接入 Hardhat 的上链、读链脚本
archive/                早期实验、旧 PPT、旧报告和讨论记录
```

三案例已完成账本复算、独立 Python 信号与成交重放、市场状态分析及 v2 审计包生成，支持换电脑运行。独立对照结果在 `final_project/cases/independent_validation.json`。原 MA60 v1 包保留用于历史核对。Argo 修复版本仍需工程复跑；Hardhat 尚未整合，三个案例也尚无链上凭据。

这个仓库是最终协作入口。同学原仓库中的合约和 Hardhat 工程通过 PR 接入这里。旧 PPT 位于历史目录，更新前请勿直接用于展示。

## 同学从这里开始

先按[任务说明](docs/给同学的任务说明.md)运行现有分析，确认结果。接下来优先把你已有的 Hardhat 合约工程接入本仓库，完成本地链存证与篡改验证；Argo 修复版本和关键测试可以并行复核。平台工作量大时，Qiyuan 可分担代码、测试和环境整理，再由另一人复核。具体步骤、命令、证据要求与未完成项都写在任务说明中。
