"""从三份分析结果生成中文对照表，数值全部从 JSON 读取。"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
CASES = [("ma60", "MA60 简单均线"), ("ema20", "EMA20 指数均线"),
         ("williams14", "Williams %R 14")]
data = {name: json.loads((BASE / name / "regime_summary.json").read_text(encoding="utf-8"))
        for name, _ in CASES}
benchmark = data["ma60"]["whole_period"]
lines = ["# 三个候选策略与买入持有基准", "",
         "这三个账户分别回测，没有合并成一个多策略组合。策略经过历史探索后选定；结果用于描述和比较，不是独立样本外验证。", "",
         "## 全期表现", "",
         "基准是初始资金 BTC/ETH 各半、首日开盘扣费买入、之后不调仓的自建组合，不是正式发布的市场指数。", "",
         "| 策略 | 累计收益 | 最大回撤 | 比基准多赚（百分点） | 相对财富增长 | 成交数 |",
         "|---|---:|---:|---:|---:|---:|",
         f"| 买入持有基准 | {benchmark['benchmark_return']*100:+.2f}% | {benchmark['benchmark_mdd']*100:.2f}% | 0.00 | 0.00% | 2 |"]
for name, label in CASES:
    w = data[name]["whole_period"]
    lines.append(f"| {label} | {w['strategy_return']*100:+.2f}% | {w['strategy_mdd']*100:.2f}% | {w['return_difference_percentage_points']:+.2f} | {w['relative_wealth_return']*100:+.2f}% | {w['strategy_trades']} |")
lines += ["", "“比基准多赚”是两者累计收益率相减；“相对财富增长”是策略期末财富除以基准期末财富再减一。二者都不是年化收益，也不是扣除市场风险后的 alpha。", "",
          "## 分市场状态", "",
          "状态用前一天可知的 BTC 过去 30 天涨跌划分；“下跌”表示近期已经下跌后的交易日，不是完整熊市。状态日可能不连续。1 bp = 0.01%。", ""]
for regime in ("上涨", "下跌", "震荡"):
    lines += [f"### {regime}", "",
              "| 策略 | 天数 | 有仓天数 | 平均开盘敞口 | 平均日净收益 bp | 基准 bp | 平均日超额 bp |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for name, label in CASES:
        r = next(x for x in data[name]["regimes"] if x["regime"] == regime)
        lines.append(f"| {label} | {r['days']} | {r['strategy_invested_days']} | {r['strategy_mean_effective_open_exposure']*100:.2f}% | {r['strategy_mean_daily_bps']:+.2f} | {r['benchmark_mean_daily_bps']:+.2f} | {r['active_mean_daily_bps']:+.2f} |")
    lines += ["", "| 策略 | 单位敞口价格贡献 bp | 单位敞口费用扣减 bp | 单位敞口净收益 bp |",
              "|---|---:|---:|---:|"]
    for name, label in CASES:
        r = next(x for x in data[name]["regimes"] if x["regime"] == regime)
        lines.append(f"| {label} | {r['strategy_gross_price_bps_per_unit_exposure']:+.2f} | {-r['strategy_fee_bps_per_unit_exposure']:.2f} | {r['strategy_net_bps_per_unit_exposure']:+.2f} |")
    lines.append("")
lines += ["## 怎样理解", "",
          "MA60 在近期下跌状态大多持有现金；EMA20 在该状态仍有少量持仓，价格变动贡献为负；Williams14 持仓更多，价格贡献为正。这些是账本中的差异，尚不能仅凭此表判断哪个信号有预测能力，或认定损益一定由某种交易行为造成。", "",
          "费用列是扣减。单位敞口指标把收益或费用之和除以每日开盘有效敞口之和；敞口很小时数值会被放大，卖出后当天无仓位也仍可能有费用。看原始日收益和有仓天数比只看这个比值更稳妥。", "",
          "三组已完成账本与每日损益核对；另用 independent_replay.py 从行情独立计算指标、信号及交易，逐笔对齐结果见 independent_validation.json。计算一致性不等于独立样本外有效性，也不替代 Argo 构建版本与完整测试的复核。", "",
          "每个案例目录的 audit_package.json 保存交易与净值；case_summary.json 保存包哈希和对账误差。新包为 v2，记录了来源账本和配置指纹，哈希与原 MA60 v1 包不同；均尚未取得链上凭据。"]
(BASE / "three_cases.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
(BASE / "three_cases.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("已更新 cases/three_cases.md 和 three_cases.json")
