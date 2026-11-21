"""Render the actual three-case analysis as a presentation-ready PNG."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CASES = [('ma60', 'MA60', '#9a4332'), ('ema20', 'EMA20', '#286876'),
         ('williams14', 'Williams14', '#92742a')]
summaries = {k: json.loads((ROOT / 'final_project/cases' / k / 'regime_summary.json').read_text(encoding='utf-8')) for k, _, _ in CASES}
daily = {k: pd.read_csv(ROOT / 'final_project/cases' / k / 'regime_daily.csv', parse_dates=['day']) for k, _, _ in CASES}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 12,
                     'text.color': '#242623', 'axes.labelcolor': '#676b65',
                     'xtick.color': '#676b65', 'ytick.color': '#676b65'})
fig = plt.figure(figsize=(16, 9), dpi=160, facecolor='#faf9f5')
fig.text(.055, .948, 'Strategy analysis', fontsize=27, weight='bold')
fig.text(.945, .955, 'GROUP 27  /  ARGO RESEARCH EXTENSION', ha='right', fontsize=10, color='#676b65')
fig.text(.055, .905, 'BTC + ETH  |  01 Jan 2022 – 31 Oct 2026  |  10,000 USDT per strategy account', fontsize=12, color='#676b65')
fig.add_artist(plt.Line2D([.055,.945],[.881,.881],transform=fig.transFigure,color='#d8d6ce',lw=1))

ax = fig.add_axes([.075,.525,.50,.285], facecolor='#faf9f5')
fig.text(.055,.844,'01  Strategy vs buy-and-hold',fontsize=16,weight='bold')
for key,label,color in CASES:
    df=daily[key]
    ax.plot(df.day,df.strategy_nav/10000,color=color,lw=1.8,label=label)
df=daily['ma60']
ax.plot(df.day,df.benchmark_nav/10000,color='#898e87',ls='--',lw=1.5,label='Buy & hold')
ax.set_ylabel('Account value / initial capital',fontsize=10)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v,p:f'{v:.1f}×'))
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.set_xlim(df.day.iloc[0], df.day.iloc[-1])
ax.set_yticks(np.arange(.5, 2.1, .5))
ax.tick_params(labelsize=10,length=0,pad=8)
ax.grid(axis='y',color='#e5e3dc',lw=.65)
for sp in ax.spines.values(): sp.set_visible(False)
ax.legend(loc='upper left',frameon=False,ncol=2,fontsize=9)

def table(rect, headers, rows, xs, widths=None, size=11, colors=None):
    a=fig.add_axes(rect); a.axis('off')
    for x,h in zip(xs,headers): a.text(x,.92,h,fontsize=size-1,color='#676b65',va='top')
    a.axhline(.78,color='#b8b8af',lw=.9)
    rowheight=.66/max(len(rows),1)
    for i,row in enumerate(rows):
        y=.67-i*rowheight
        for j,(x,v) in enumerate(zip(xs,row)):
            a.text(x,y,str(v),fontsize=size,va='center',color=(colors[i] if j==0 and colors else '#242623'))
        a.axhline(y-rowheight*.52,color='#e1dfd7',lw=.6)
    return a

fig.text(.63,.844,'Full-period results',fontsize=16,weight='bold')
rows=[]
for key,label,color in CASES:
    w=summaries[key]['whole_period']; rows.append([label,f"{w['strategy_return']:+.1%}",f"{w['strategy_mdd']:.1%}"])
w=summaries['ma60']['whole_period']
rows.append(['Buy & hold',f"{w['benchmark_return']:+.1%}",f"{w['benchmark_mdd']:.1%}"])
table([.63,.565,.315,.235],['Account','Return','Max drawdown'],rows,[0,.40,.70],size=12,
      colors=[x[2] for x in CASES]+['#676b65'])
fig.text(.63,.52,'Benchmark: 50% BTC / 50% ETH at entry; buy fees included.\nHold thereafter, with no rebalancing.',fontsize=9,color='#676b65',linespacing=1.5)

fig.add_artist(plt.Line2D([.055,.945],[.465,.465],transform=fig.transFigure,color='#d8d6ce',lw=1))
fig.text(.055,.421,'02  Market conditions · MA60',fontsize=16,weight='bold')
fig.text(.055,.389,'How much capital was actually invested?',fontsize=11,color='#676b65')
labels={'上涨':'Recent rise','下跌':'Recent decline','震荡':'Limited move'}
rows=[]
for r in summaries['ma60']['regimes']:
    rows.append([labels[r['regime']],str(r['days']),f"{r['strategy_mean_effective_open_exposure']:.1%}",
                 str(r['days']-r['strategy_invested_days']),f"{r['strategy_mean_daily_bps']:+.2f}"])
table([.055,.145,.45,.215],['Condition','Days','Exposure','Flat days','Net/day¹'],rows,[0,.30,.43,.64,.83],size=10.5)

fig.text(.55,.421,'03  Price moves and fees · recent decline',fontsize=16,weight='bold')
fig.text(.55,.389,'329 days in the same condition; daily contributions in bp',fontsize=11,color='#676b65')
rows=[]
for key,label,color in CASES:
    r=next(x for x in summaries[key]['regimes'] if x['regime']=='下跌')
    price=r['strategy_mean_gross_price_daily_bps']; fee=r['strategy_mean_fee_daily_bps']; net=r['strategy_mean_daily_bps']
    assert abs(price-fee-net)<1e-7
    rows.append([label,f"{r['strategy_mean_effective_open_exposure']:.1%}",f'{price:+.2f}',f'{-fee:.2f}',f'{net:+.2f}'])
table([.55,.145,.395,.215],['Strategy','Exposure','Price/day','Fees/day','Net/day'],rows,[0,.28,.49,.69,.88],size=10.5,
      colors=[x[2] for x in CASES])
fig.text(.055,.122,'Exposure = position value after opening fills / previous NAV.  Flat days = no opening position.',fontsize=9,color='#676b65')
fig.text(.55,.122,'Price/day + Fees/day = Net/day; checked against daily NAV.',fontsize=9,color='#676b65')
fig.add_artist(plt.Line2D([.055,.945],[.095,.095],transform=fig.transFigure,color='#d8d6ce',lw=1))
fig.text(.055,.065,'Conditions: prior 30-day BTC return, known at t−1; rise >10%, decline <−10%, otherwise limited move. First 31 days unclassified.',fontsize=9,color='#676b65')
fig.text(.055,.038,'¹ Net/day is in basis points (1 bp = 0.01%). Historical descriptive analysis; not an out-of-sample test or risk-adjusted alpha.',fontsize=9,color='#676b65')
fig.text(.945,.018,'ACTUAL SCRIPT OUTPUT · NOT AN ARGO NATIVE SCREEN',fontsize=8,color='#676b65',ha='right')
path=OUT/'analysis_demo.png'
fig.savefig(path,dpi=160,facecolor=fig.get_facecolor())
print(path)
