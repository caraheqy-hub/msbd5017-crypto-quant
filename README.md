# 加密策略研究工具：回测、分析与可验证记录

MSBD5017 · Group 27 · HE Qiyuan、ZHANG Xinyue

我们基于 Argo 做一个策略研究工具原型。研究者不仅要得到收益曲线，还要检查信号为何产生、交易如何执行、不同实验为什么有差异，并保存能交给别人核查的记录。

**回测记录上链与链上核验是平台的正式功能之一，由 ZHANG Xinyue 主导。** 研究者生成审计包后，可提交包哈希，保存链上凭据，并让审核者读链比对文件；当前已有包和脚本，工程集成与实际链上验证仍待完成。

MA60、EMA20、Williams14 是三个演示案例，用来检验同一研究流程能否支持不同规则。历史收益是案例输出，项目的目标是完善研究流程，并非推荐收益最高的策略。

## 从这里开始

| 想了解什么 | 阅读入口 |
|---|---|
| 项目解决什么问题，当前做到了哪里 | [项目说明](项目说明.md) |
| Argo 提供什么、我们做了什么、还计划做什么 | [功能范围与开发计划](docs/功能范围与开发计划.md) |
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
scripts/                待接入 Hardhat 的上链和读链脚本
presentations/interim/  当前两分钟汇报及讲稿
archive/                早期实验与讨论，不代表当前结论
```

已完成：三案例计算对照、账户检查、结果比较及审计包。待完成：研究功能界面与接口、Argo 构建版本复核、Hardhat 集成和实际链上凭据。详细状态以功能范围文档为准。这个仓库是最终协作入口，旧 PPT 已归档。
