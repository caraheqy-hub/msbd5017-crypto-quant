> 历史记录：本文保留当时的判断和数字，部分结论后来已修正。当前项目请从仓库根目录 README.md 阅读。

# Three-minute interim report script (English) — real Binance data

**Slide 1, about 30 seconds**
Good afternoon. We are Group 27, Qiyuan He and Xinyue Zhang. Our project asks how to make a crypto strategy backtest reproducible and auditable. A performance chart alone does not tell a reader which data, strategy rules, fees, or trades produced it. We freeze those records, hash them, and show that any later change can be detected.

**Slide 2, about 50 seconds**
We ran a causal portfolio experiment on real Binance daily BTC and ETH spot prices from January 2022 through October 2026. We compare buy and hold, an equal-weight portfolio, a moving-average trend rule, a short-term reversal rule, and a blend of the last two. Every strategy uses the same dates and a ten-basis-point fee per unit of turnover. Signals use yesterday's close, simulated fills occur at today's close, and returns start tomorrow. We hold out the last 30 percent of observations, and we label bull, bear, and sideways conditions using only the previous 30 days of BTC returns, so the comparison across market conditions is causal and not using future information.

**Slide 3, about 55 seconds**
On about 1,700 comparable daily observations, the trend strategy performs best in the holdout: it returns roughly 25 percent with a Sharpe of 0.65 and a maximum drawdown of about 31 percent. Its mean daily net return is positive in each of the three past-return market regimes. The blend also finishes slightly positive at 0.6 percent. Buy and hold made about 137 percent in development but lost about 26 percent in the holdout; mean reversion and equal weight also lost money. These results address the across-market-condition comparison, although one historical window cannot establish that the pattern will persist. Every input, code, trade, and output is hashed into one root digest, and verification recomputes those digests, so an altered record fails the check.

**Slide 4, about 35 seconds**
Next we record paper orders, fills, and slippage, then deploy the anchor contract to a testnet and verify against a tampered record. We will add live exchange data only after the historical backtest passes, using Binance for spot and modeling OKX DEX separately. We may use Argo to cross-check strategies, but the Python audit record remains the reproducible reference. Thank you.

**If asked:** OKX centralized perpetual SWAP data and OKX DEX Swap on-chain data are different products with different execution, funding, gas, and liquidity; we will choose one only after specifying its mechanics and costs, and will not mix them in one backtest.
