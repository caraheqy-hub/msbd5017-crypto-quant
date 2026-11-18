"""Rebuild the interim deck with REAL Binance backtest results."""
from pathlib import Path
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

HERE = Path(__file__).resolve().parent
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
NAVY = RGBColor(20, 35, 58)
TEAL = RGBColor(4, 137, 133)
GRAY = RGBColor(79, 91, 106)
WHITE = RGBColor(255, 255, 255)
PALE = RGBColor(232, 244, 242)


def box(slide, x, y, w, h, fill):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.fill.background()
    return shape


def text(slide, s, x, y, w, h, size=22, color=NAVY, bold=False, align=None):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(.04)
    p = tf.paragraphs[0]
    p.text = s
    p.font.name = "Aptos"
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    if align:
        p.alignment = align
    return shape


def slide(title, number):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    box(s, 0, 0, .16, 7.5, TEAL)
    text(s, title, .62, .38, 11.9, .65, 30, NAVY, True)
    text(s, f"MSBD 5017  /  GROUP 27  /  {number}", .64, 7.05, 11.8, .23, 10, GRAY)
    return s


# Slide 1 — title
s = slide("Can we verify a crypto backtest after publication?", "01")
text(s, "Blockchain-anchored multi-strategy portfolio backtesting", .7, 1.48, 11.7, .7, 26, TEAL, True)
text(s, "HE Qiyuan  ·  ZHANG Xinyue", .72, 2.4, 10.8, .5, 23)
box(s, .7, 3.5, 11.7, 1.35, PALE)
text(s, "Research question", 1.0, 3.72, 3.0, .45, 20, TEAL, True)
text(s, "Can identical inputs and rules reproduce portfolio results, and can a changed record be detected?", 3.6, 3.64, 8.3, .82, 22)
text(s, "Interim report  ·  21 November 2026  ·  historical backtest on real Binance data", .72, 5.65, 11.7, .45, 18, GRAY)

# Slide 2 — method
s = slide("A causal comparison, then an audit trail", "02")
stages = [
    ("1  Data", "Real BTC/ETH daily spot\nJan 2022 - Oct 2026\nFrozen CSV + SHA-256"),
    ("2  Portfolio", "Buy and hold, equal weight,\ntrend, reversal, blend"),
    ("3  Evaluation", "Same fees and dates\n70/30 development / holdout\nPast-return market regimes"),
    ("4  Verification", "Trades + results hashed\nRoot prepared for testnet"),
]
for i, (head, body) in enumerate(stages):
    x = .64 + 3.13*i
    box(s, x, 1.55, 2.9, .13, TEAL)
    text(s, head, x, 1.91, 2.9, .43, 20, TEAL, True)
    text(s, body, x, 2.5, 2.85, 2.15, 17)
text(s, "Signals use yesterday's close; simulated fills occur at today's close; returns start tomorrow.", .7, 5.44, 11.9, .9, 19, NAVY, True)

# Slide 3 — results
s = slide("Real data: trend leads in the holdout", "03")
text(s, "Sample", .7, 1.5, 2.2, .45, 21, TEAL, True)
text(s, "1,704 daily observations  ·  1,192 development / 512 holdout  ·  10 bp fee per turnover", .72, 2.0, 11.5, .5, 19)
text(s, "Trend  (20/60-day moving average)", .7, 2.72, 6.4, .5, 21, TEAL, True)
text(s, "+25.3% holdout return  ·  Sharpe 0.65  ·  max drawdown -30.8%\npositive mean daily net return in all three past-return regimes", .74, 3.2, 6.4, 1.15, 18)
text(s, "Other holdout results", .7, 4.5, 6.4, .5, 21, TEAL, True)
text(s, "BTC hold  +137% in-sample  →  -25.6% holdout\nBlend +0.6%  ·  reversal -23.6%  ·  equal-weight -16.2%", .74, 4.98, 6.4, 1.1, 17)
box(s, 7.5, 2.72, 5.15, 3.35, PALE)
text(s, "Audit check", 7.78, 2.92, 2.4, .45, 19, TEAL, True)
text(s, "One root ac9feba0... hashes inputs,\ncode, trades and outputs.\nverify recomputes every digest;\nchanging a trade fails.", 7.82, 3.5, 4.6, 2.3, 18)
text(s, "One 4.8-year window, two assets - no claim of statistical significance.", .72, 6.3, 11.7, .46, 14, GRAY)

# Slide 4 — next steps
s = slide("What we will validate before the final report", "04")
items = [
    ("01", "Real history", "Done: frozen Binance spot candles, verified root digest."),
    ("02", "Execution", "Record paper orders, fills, slippage after the historical run passes."),
    ("03", "On-chain proof", "Publish the digest on a testnet; verify it against a modified record."),
    ("04", "Live data", "Only after the backtest works - Binance API; OKX DEX modeled separately."),
]
for i, (n, head, body) in enumerate(items):
    y = 1.42 + 1.32*i
    text(s, n, .7, y, .8, .5, 20, TEAL, True)
    text(s, head, 1.55, y, 2.5, .5, 20, NAVY, True)
    text(s, body, 4.1, y, 8.4, .95, 18)
text(s, "Argo may cross-check strategies on macOS; the Python audit record stays the reproducible reference.", .72, 6.75, 11.75, .45, 13, GRAY)

output = HERE / "interim_group27_2026-11-21.pptx"
prs.save(output)
print(output)
