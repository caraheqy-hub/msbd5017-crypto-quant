# BTC/ETH 策略回测与链上存证

MSBD5017 · Group 27 · HE Qiyuan、ZHANG Xinyue

我们研究一个简单的问题：用均线决定何时持有比特币和以太坊，比一直持有表现如何？然后把数据版本、交易记录和每日账户净值整理成一份文件，供别人重算，并准备将文件指纹写到区块链上，方便核查它后来有没有被改过。

## 从哪里开始看

| 你想了解什么 | 看这里 |
|---|---|
| 项目为什么做、目前做到了哪里 | [项目说明](项目说明.md) |
| 两个人各做什么、下一步怎么提 PR | [分工与验收](docs/分工与验收.md) |
| 当前回测的规则和结果怎么理解 | [实验方法与结果](final_project/README.md) |
| 审计包是什么、怎样检查 | [审计包说明](audit/README.md) |
| 以前讨论过什么、数字为什么变过 | [历史材料](archive/README.md)；这些不是当前结论 |

## 先运行已有的分析

在仓库根目录执行，需要 Python 3.10 或以上：

```powershell
python -m pip install -r requirements.txt
python final_project/regime_analysis.py --prices final_project/input/btc_eth_daily.parquet --audit-package audit/audit_package.json --output-dir final_project/output
python audit/verify_local.py
```

第一条分析命令读取已保存的 MA60 回测账户净值，重新计算基准、市场状态和收益拆分；它不会重新运行 Argo 引擎。输出在 `final_project/output/`。第二条命令检查本地审计包的哈希，并在内存中修改一笔交易，演示如何发现变化。

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

当前已完成历史回测结果对账、市场状态分析和本地哈希检查。Argo 引擎改动还需要同学复核；包的生成脚本仍有本机路径；本仓库还未整合 Hardhat 工程，也没有当前审计包的链上交易凭据。这些是下一步共同完成的内容。

这个仓库是最终协作入口。同学原仓库中的合约和 Hardhat 工程通过 PR 接入这里。旧 PPT 位于历史目录，更新前请勿直接用于展示。
