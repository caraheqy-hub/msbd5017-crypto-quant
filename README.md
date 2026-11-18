# MSBD 5017: auditable crypto portfolio backtest

Group: HE Qiyuan, ZHANG Xinyue. Interim report: 21 November 2026.

This is a research prototype. Its core question is whether a reader can reproduce a multi-strategy crypto backtest and detect later changes to its input, parameters or trades. Hashing alone provides local integrity; the Solidity contract can publish the final digest on a chain, but has **not** been deployed.

## Run

Python 3.10+ with the standard library is sufficient.

```powershell
python .\crypto_project\backtest.py demo --out .\crypto_project\outputs\demo
python .\crypto_project\backtest.py verify --out .\crypto_project\outputs\demo
```

`data/binance_spot_daily.csv` is the frozen real Binance BTC/ETH spot dataset (2022-01-01 through 2026-10-31). `outputs/real` contains its verified results. `demo` remains a deterministic **synthetic** engineering check. To refresh real data on a machine with Binance access, run:

```powershell
python .\crypto_project\backtest.py fetch --start 2022-01-01 --end 2026-11-01 --out .\crypto_project\data\binance_spot_daily.csv
python .\crypto_project\backtest.py run --csv .\crypto_project\data\binance_spot_daily.csv --out .\crypto_project\outputs\real
python .\crypto_project\backtest.py verify --out .\crypto_project\outputs\real
```

The public endpoint needs no key. Keep raw CSV and `audit.json` together. The fetch command records UTC daily close prices and excludes incomplete candles. `run` accepts a CSV with `date,symbol,close` columns, one close per asset/day; it requires aligned BTCUSDT and ETHUSDT dates, strictly positive prices and at least 120 observations.

## Design and limits

- Universe: BTCUSDT and ETHUSDT spot, with USDT cash. No leverage, shorts, funding or gas. The DEX comparison is future work, not a proxy using OKX centralized SWAP candles.
- Strategies: BTC buy-and-hold, equal-weight BTC/ETH, dual moving-average trend (20/60 days), five-day mean reversion, and a 50/50 blend of the latter two. Each uses the same dates and fee model.
- Timing: the signal is calculated from data available through yesterday's close. It trades at today's close, paying 10 basis points on absolute weight turnover, and earns tomorrow's close-to-close return. This timing is conservative but today's close fill is an idealization; spread, market impact, and latency are not modeled.
- Splits: first 70% of comparable daily observations are development, final 30% are held out. Parameters are fixed in code before inspection of the holdout. Regimes use the *past* 30-day BTC return: bull above +10%, bear below -10%, otherwise sideways. This causal label is descriptive, not an ex-post classification of future market conditions.
- Metrics: total return, annualized volatility, Sharpe (zero risk-free rate), maximum drawdown, and observation count. Regime comparison uses mean daily net returns and days. There is no claim of statistical significance or optimality.
- Audit: `audit.json` includes SHA-256 digests of the exact input CSV bytes, code bytes and canonical `trades.json` bytes, plus config, metrics and a final root hash. `verify` recomputes every digest and the root. The root can be passed to `BacktestAnchor.sol`; an emitted event then attests to the earlier root, while raw files must be preserved off-chain for independent replay. The contract cannot prove data quality or strategy profitability.

## Next steps for final project

1. Review and extend the frozen Binance spot study. The current real-data holdout has 512 comparable days: trend +25.3%, blend +0.6%, BTC hold -25.6%, equal weight -16.2%, reversal -23.6%. The trend rule has positive mean daily net returns in each of the three causal market regimes; this single historical window does not establish significance or future profitability.
2. Add a paper-order adapter only after the historical run passes. Record order, fill, timestamp, fees and slippage separately.
3. Decide whether the comparison needs OKX *DEX aggregator* on-chain token data or OKX centralized perpetual SWAP data. They have different execution, funding, gas and liquidity assumptions, so do not mix them in the same backtest without an explicit model.
4. Deploy the anchor contract to a testnet, submit the root, save chain ID, address and transaction hash, then demonstrate a modified trade failing verification.

Sources: [Binance public market-data API](https://developers.binance.com/en/docs/products/spot/rest-api), [Argo Trading framework](https://github.com/rxtech-lab/argo-trading), [OKX DEX Swap API](https://web3.okx.com/ko/onchainos/dev-docs/trade/dex-swap).
