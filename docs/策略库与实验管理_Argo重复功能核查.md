# 策略库与实验管理：Argo 已有功能核查

日期：2026-11-20。目的：确认哪些能力应复用，避免把 Argo 已有功能重新开发或当成新贡献。

## 结论

**不要从零再做一个策略列表、参数配置器、回测历史列表或 AI 跑回测入口。Argo 已有这些能力。** 官方还提供同一策略历史结果汇总、运行 ID、配置快照、WASM 内容哈希缓存及 AI 配合 Python 分析的工作流程。

“个人因子库”应收窄成研究管理扩展：在原有策略和回测记录上补来源、假设、研究结论、版本关系和试验状态。相似度诊断可作为后续独立分析工具。下述缺口是候选需求，不是本项目已完成的功能。

## 核查范围与证据强度

读取两个官方仓库的 main 目录树，固定版本：

- 核心：`5000407e138e3d38bfa98f3318e02dd4fdbcaa17`。
- macOS：`5a69473c26627b526dcf53c14c753e10cb7f2a77`。

重点检查策略服务/元数据、schema、项目文档、历史结果服务与界面、回测执行/输出、MCP 工具目录与处理器、官方 AI 使用指南。另对仓库搜索 correlation、similarity、parent_run，以及 macOS 的 research_status、source_url、optimizer。相关关键词未命中只能辅助判断，不能证明所有分支、发布包或插件均无对应功能。本次没有在 Mac 实际操作。

## 逐项核查

| 先前建议 | Argo 的实际实现 | 判断与处理 |
|---|---|---|
| 个人策略列表 | StrategyService 列出、导入、重命名、删除 WASM；MCP 也能列出策略 | **已有，直接复用** |
| 策略名称、说明、参数卡片 | StrategyMetadata 有 Identifier、Name、Description、Schema、RuntimeVersion，界面展示 | **已有基础，不能再申报为完整新增** |
| 来源、研究假设、结论、类别 | Description 可以写自由文本；所查结构未见独立的来源 URL、研究状态与审核结论字段 | 可补结构化字段与筛选，不是首次允许写说明 |
| 参数与配置管理 | Schema 保存参数、引擎配置、策略路径、创建/更新时间；可以增删改；MCP 可读写 | **已有，直接复用** |
| 实验历史 | 结果按日期与策略读取；History 列表可进入图表/明细，也可删除 | **已有，直接复用** |
| 每次回测的 run_id | 核心每个策略×配置×数据组合生成 UUID，保存结果 ID；会话目录含时间 | **已有，不新建另一套 ID 代替它** |
| 配置快照 | writeResults 把引擎配置和策略配置写入 stats.yaml | **已有，应读取原记录** |
| 基础结果比较 | 策略概览汇总多次结果的最好/最差/平均收益、胜率、回撤、费用、币种表现、相对买入持有差异 | **已有基础；“结果比较”不能笼统算新增** |
| 成对实验差异诊断 | 所查页面是历史列表和汇总；未发现成对参数差异、输入文件差异与结果差异联合诊断 | 可补明确范围；不要把现有汇总说成没有比较 |
| 批量参数回测 | 核心接受多个策略、配置和数据路径，遍历组合运行；macOS 当前选中 schema 的入口传一个配置 | **核心已有批量基础**，不等于已提供搜索算法或全量研究账本 |
| 失败与落选试验留存 | macOS 累积错误、显示失败，MCP 返回错误；核心遇到 runSingleIteration 错误会返回 | **错误反馈已有**；所查路径未见持久化的全试验清单、淘汰原因和搜索预算记录，可补研究台账 |
| 策略版本管理 | 有标识、运行时 API 版本和兼容性检查；结果也有策略信息 | **部分已有**；运行时版本不是策略源码提交，不能混用 |
| 文件哈希 | StrategyCacheService 对 WASM 计算 SHA-256，以内容变化使缓存失效 | **哈希机制已有**；这段缓存逻辑不等于每次回测的不可变源文件快照 |
| 完整实验来源追踪 | 结果记录路径、配置和策略信息；官方建议改写前手动备份 WASM | 所查路径未发现自动保存每次源码/WASM/数据快照与父子版本关系；可补绑定、归档与验证 |
| 策略收益相关性/持仓重合 | 所查数据模型、界面和 MCP 目录未见专用计算入口；两仓 correlation/similarity 搜索未命中 | **本次未发现，可作为后续分析扩展**；先定义对齐区间、缺失处理、仓位与样本限制 |
| IC 双门槛和因子去重 | 未发现对应筛选工作流 | 不直接照搬 A 股平台阈值；当前 BTC/ETH 时序策略不等于横截面因子库 |
| AI 操作策略与回测 | 官方 MCP 已支持导入策略、配置读写、选数据、执行回测、状态查询、历史结果查询 | **已有，不再另造通用 AI 入口** |
| AI 配合 Python 分析 | docs/Skills.md 已写明 agent 编写策略、运行回测、读取 stats/Parquet、用 Python/DuckDB 分析 | **官方已有流程**；我们的贡献只能是具体分析算法及工具封装，不是首次用 AI/Python 看结果 |
| 故障排查知识 | 官方已有文档、日志、错误和测试；我们的真实修复可形成复现案例 | 可贡献具体问题手册，不宣称首创诊断体系 |

## 容易混淆的四点

1. **引擎版本不等于策略版本。** RuntimeVersion 表示编译所用引擎 API，不自动代表某个策略源代码的 Git 提交。
2. **缓存哈希不等于研究归档。** 内容哈希能发现文件变动，但是否保存旧文件、对应哪次实验，需要另一层记录。
3. **历史结果不等于所有研究尝试。** 用户仍可删结果；失败、未跑、放弃、筛掉的候选，不一定形成可审查的完整台账。
4. **已有比较不等于已有我们的诊断。** 平均收益等汇总已经有，新增必须具体到状态、敞口、损益拆分或成对输入差异等任务。

## 建议最后保留哪些开发内容

### 直接复用

沿用策略导入、元数据、Schema、原生 run ID、配置快照、历史结果和 MCP。用现有接口关联我们的分析输出，不做第二套基础管理系统。

### 优先补充

- **现有结果诊断模块**：继续完善状态、敞口、价格损益与费用分析。这已有脚本，不是新许愿。
- **研究备注与决策记录**：给现有策略/运行补来源、假设、结论、保留/放弃原因；按原生 ID 关联。
- **输入与构建来源记录**：绑定确切源码、WASM、行情及结果指纹，保留必要快照；不把缓存哈希包装成这项能力。

### 后续再做

- 全试验清单与版本关系：先界定研究预算、失败/淘汰记录和不可覆盖要求。
- 相似度：同区间每日收益相关性与持仓重合分析，不设置没有验证依据的统一通过门槛。
- AI 工具：在现有 MCP 上追加我们的具体分析调用，不开发一个重复的 AI 回测入口。

以上扩展均应先用一个真实任务验收，例如“找到 MA60 改动前后的两次运行，说明输入改了什么、结果差在哪里”。不以多建一个列表或多加一个按钮作为贡献。

## 对现有代码的影响

`final_project/run_record.py` 是固定案例的辅助脚本，不能当作 Argo 缺少实验记录的证据。继续开发前应改为关联原生 run ID，获取真实源码/工作区信息，并处理重复运行覆盖。历史案例若未保留原生 ID，需明确标为外部导入记录，不能伪造关联。

不要把“完整个人因子库”“AI 研究助手”“相似度系统”列为已经交付。当前可交付的是具体计算修复、三个案例的独立复算、结果诊断脚本及审计包。

## 关键源码位置

- [策略服务](https://github.com/rxtech-lab/argo-trading-macOS/blob/5a69473c26627b526dcf53c14c753e10cb7f2a77/ArgoTradingSwift/Services/StrategyService.swift)：导入/列表/重命名/删除。
- [策略元数据与历史汇总](https://github.com/rxtech-lab/argo-trading-macOS/blob/5a69473c26627b526dcf53c14c753e10cb7f2a77/ArgoTradingSwift/Views/Backtest/Strategy/StrategyMetadataView.swift)：元数据、收益/风险/费用/基准汇总。
- [历史结果界面](https://github.com/rxtech-lab/argo-trading-macOS/blob/5a69473c26627b526dcf53c14c753e10cb7f2a77/ArgoTradingSwift/Views/Backtest/Strategy/StrategyResultsListView.swift)：History、图表和明细。
- [Schema 数据结构](https://github.com/rxtech-lab/argo-trading-macOS/blob/5a69473c26627b526dcf53c14c753e10cb7f2a77/ArgoTradingSwift/Models/Schema.swift)：参数与时间字段。
- [回测核心](https://github.com/rxtech-lab/argo-trading/blob/5000407e138e3d38bfa98f3318e02dd4fdbcaa17/internal/backtest/engine/engine_v1/backtest_v1.go)：Run 的组合循环与 UUID，writeResults 的配置快照。
- [WASM 哈希缓存](https://github.com/rxtech-lab/argo-trading-macOS/blob/5a69473c26627b526dcf53c14c753e10cb7f2a77/ArgoTradingSwift/Services/StrategyCacheService.swift)：getMetadata 与 computeContentHash。
- [元数据 API](https://github.com/rxtech-lab/argo-trading/blob/5000407e138e3d38bfa98f3318e02dd4fdbcaa17/pkg/swift-argo/strategy.go)：RuntimeVersion 的定义。
- [MCP 工具目录](https://github.com/rxtech-lab/argo-trading-macOS/blob/5a69473c26627b526dcf53c14c753e10cb7f2a77/ArgoTradingSwift/MCP/MCPToolCatalog.swift)、[处理器](https://github.com/rxtech-lab/argo-trading-macOS/blob/5a69473c26627b526dcf53c14c753e10cb7f2a77/ArgoTradingSwift/MCP/MCPToolHandlers.swift)：实际开放的操作。
- [官方 AI 工作流程](https://github.com/rxtech-lab/argo-trading-macOS/blob/5a69473c26627b526dcf53c14c753e10cb7f2a77/docs/Skills.md)：策略迭代、手动备份与 Python 分析。
