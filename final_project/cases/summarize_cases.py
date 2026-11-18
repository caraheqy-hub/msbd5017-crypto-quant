"""Combine the three case results into one Markdown + JSON summary."""
import json
from pathlib import Path

BASE = Path(__file__).parent
CASES = [("ma60", "MA60 简单均线"), ("ema20", "EMA20 指数均线"), ("williams14", "Williams %R 14")]

data = {}
for name, label in CASES:
    data[name] = json.loads((BASE / name / "regime_summary.json").read_text(encoding="utf-8"))

lines = ["# 三个候选策略的同口径比较", ""]
lines.append("> 描述性结果。策略与阈值不是独立样本外确定的；分状态是条件平均，不是三段区间的累计收益。")
lines.append("")

lines.append("## 全期")
lines.append("")
lines.append("| 策略 | 累计收益 | 最大回撤 | 成交数 |")
lines.append("|---|---:|---:|---:|")
for name, label in CASES:
    wp = data[name]["whole_period"]
    lines.append(f"| {label} | {wp['strategy_return']*100:+.2f}% | {wp['strategy_mdd']*100:+.2f}% | {wp['strategy_trades']} |")

lines.append("")
lines.append("## 分市场状态（条件平均日收益，单位 bp）")
lines.append("")
for regime in ("上涨", "下跌", "震荡"):
    lines.append(f"### {regime}")
    lines.append("")
    lines.append("| 策略 | 天数 | 有仓天数 | 平均开盘敞口 | 净日收益 | 价格/单位敞口 | 费用/单位敞口 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for name, label in CASES:
        r = next(x for x in data[name]["regimes"] if x["regime"] == regime)
        price = "n/a" if r["strategy_gross_price_bps_per_unit_exposure"] is None else f"{r['strategy_gross_price_bps_per_unit_exposure']:+.2f}"
        fee = "n/a" if r["strategy_fee_bps_per_unit_exposure"] is None else f"{r['strategy_fee_bps_per_unit_exposure']:+.2f}"
        lines.append(
            f"| {label} | {r['days']} | {r['strategy_invested_days']} | "
            f"{r['strategy_mean_effective_open_exposure']*100:.2f}% | "
            f"{r['strategy_mean_daily_bps']:+.2f} | {price} | {fee} |"
        )
    lines.append("")

lines.append("## 怎么读")
lines.append("")
lines.append("- **MA60**：趋势最慢，下跌状态几乎空仓（329 天只 11 天有仓），净亏主要来自费用。")
lines.append("- **EMA20**：更快，交易 390 笔；下跌状态仍持仓 27 天、敞口 5.43%，价格贡献为负（追涨杀跌的代价）。")
lines.append("- **Williams14**：区间位置信号，下跌状态反而高仓位（61.26%）且价格贡献为正，更像逢跌买入；代价是回撤最大（−40.30%）。")
lines.append("- 三者是**候选策略的比较**，不是组合；组合要等各自验证后再谈。")
lines.append("- 低敞口状态（如下跌 1.52%）的单位敞口值不稳定，只作机制参考。")

markdown = "\n".join(lines) + "\n"
(BASE / "three_cases.md").write_text(markdown, encoding="utf-8")
(BASE / "three_cases.json").write_text(
    json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(markdown)
