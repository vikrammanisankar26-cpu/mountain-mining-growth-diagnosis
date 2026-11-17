"""Builds charts/*.png and results.json. Run: python src/make_charts.py"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import model as m  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "charts"
OUT.mkdir(exist_ok=True)
INK, MUTED, GRID = "#1b1f1c", "#6b726d", "#e4e1d8"
GREEN, SOFT, RED, GOLD = "#1f5c43", "#9cc3ad", "#a8432f", "#b8892b"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": GRID,
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": GRID, "axes.axisbelow": True, "figure.dpi": 160,
                     "savefig.bbox": "tight", "savefig.facecolor": "white", "text.parse_math": False})


def title(ax, main, sub):
    ax.set_title(main, loc="left", fontsize=14, fontweight="bold", color=INK, pad=26)
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=10.5, color=MUTED)


d = m.load()
r = m.ratios(d)
Y = m.YEARS

# 1. Actual vs sustainable growth
fig, ax = plt.subplots(figsize=(9, 4.6))
yy = Y[1:]
x = np.arange(len(yy))
act = [r[y]["sales_growth"] * 100 for y in yy]
sus = [r[y]["sustainable_growth"] * 100 for y in yy]
ax.bar(x - 0.2, act, 0.4, color=RED, label="Actual sales growth")
ax.bar(x + 0.2, sus, 0.4, color=GREEN, label="Sustainable growth (ROE × retention)")
for i in range(len(yy)):
    ax.text(x[i] - 0.2, act[i] + 0.6, f"{act[i]:.0f}%", ha="center", color=INK, fontweight="bold")
    ax.text(x[i] + 0.2, sus[i] + 0.6, f"{sus[i]:.1f}%", ha="center", color=INK, fontweight="bold")
ax.set_xticks(x, yy); ax.set_ylabel("%"); ax.set_ylim(0, 36); ax.legend(frameon=False, loc="upper left")
title(ax, "Growing five times faster than it can afford",
      "Sales growth vs the growth equity alone can fund at the current payout and leverage")
fig.savefig(OUT / "01_actual_vs_sustainable.png"); plt.close(fig)

# 2. Margin erosion
fig, ax = plt.subplots(figsize=(9, 4.6))
for k, lab, c in (("gross_margin", "Gross margin", SOFT), ("ebit_margin", "EBIT margin", GREEN), ("net_margin", "Net margin", RED)):
    v = [r[y][k] * 100 for y in Y]
    ax.plot(Y, v, marker="o", lw=2.5, color=c, label=lab)
    for y, val in zip(Y, v):
        ax.annotate(f"{val:.1f}%", (y, val), xytext=(0, 9), textcoords="offset points", ha="center", color=INK, fontsize=10)
ax.set_ylim(0, 30); ax.set_ylabel("% of sales"); ax.legend(frameon=False, loc="upper right")
title(ax, "Each extra dollar of sales earns less",
      "Margins fell every year while sales grew 63% over two years")
fig.savefig(OUT / "02_margin_erosion.png"); plt.close(fig)

# 3. Working capital days
fig, ax = plt.subplots(figsize=(9, 4.6))
x = np.arange(len(Y)); w = 0.26
for j, (k, lab, c) in enumerate((("dso", "Days sales outstanding", SOFT), ("dio", "Days inventory", GOLD),
                                  ("dpo", "Days payables", GREEN))):
    v = [r[y][k] for y in Y]
    ax.bar(x + (j - 1) * w, v, w, color=c, label=lab)
    for i, val in enumerate(v):
        ax.text(x[i] + (j - 1) * w, val + 1.5, f"{val:.0f}", ha="center", fontsize=9.5, color=INK)
ax.plot(x, [r[y]["cash_conversion_cycle"] for y in Y], color=RED, marker="D", lw=2, label="Cash conversion cycle")
ax.set_xticks(x, Y); ax.set_ylabel("Days"); ax.set_ylim(0, 110); ax.legend(frameon=False, ncol=2, loc="upper left")
title(ax, "Cash is getting stuck in receivables and inventory",
      "Inventory days up 30 and receivable days up 16 in two years; payables stretched from 45 to 74 days")
fig.savefig(OUT / "03_working_capital_days.png"); plt.close(fig)

# 4. Funding the 2026 asset growth
f = m.funding(d)
parts = [("Retained\nearnings", f["retained_earnings"], GREEN), ("Supplier credit\n& accruals", f["payables_and_accruals"], GOLD),
         ("New long-term\ndebt", f["new_debt"], RED), ("New equity", f["new_equity"], SOFT)]
fig, ax = plt.subplots(figsize=(9, 3.0))
left = 0
for lab, v, c in parts:
    ax.barh(0, v / 1000, left=left / 1000, color=c, height=0.5)
    if v > 0:
        ax.text((left + v / 2) / 1000, 0, f"{lab}\n${v / 1000:.0f}K · {v / f['asset_growth'] * 100:.0f}%",
                ha="center", va="center", color="white" if c in (GREEN, RED) else INK, fontsize=10)
    left += v
ax.set_yticks([]); ax.set_xlim(0, f["asset_growth"] / 1000 * 1.02); ax.set_xlabel("$ thousands")
ax.grid(axis="y", visible=False)
borrowed = (f["new_debt"] + f["payables_and_accruals"]) / f["asset_growth"]
title(ax, f"{borrowed * 100:.0f}% of 2026's ${f['asset_growth'] / 1000:.0f}K asset growth came from lenders and suppliers",
      "Sources of funding for the increase in total assets, 2025 to 2026; no new equity was raised")
fig.savefig(OUT / "04_funding_2026.png"); plt.close(fig)

# 5. Projection: what continued growth does to leverage
fig, ax = plt.subplots(figsize=(9, 4.8))
paths = [("Keep growing 30%", m.project(d, 0.30), RED, "-"),
         ("30% with zero dividends", m.project(d, 0.30, payout=0), GOLD, "--"),
         ("Slow to 15%", m.project(d, 0.15), SOFT, "-"),
         (f"Sustainable rate ({r['2026']['sustainable_growth'] * 100:.1f}%)", m.project(d, r["2026"]["sustainable_growth"]), GREEN, "-")]
for lab, p, c, ls in paths:
    xs, ys = [q["year"] for q in p], [q["debt_to_equity"] for q in p]
    ax.plot(xs, ys, color=c, lw=2.5, ls=ls, marker="o", label=lab)
    ax.annotate(f"{ys[-1]:.2f}x", (xs[-1], ys[-1]), xytext=(8, -4), textcoords="offset points", color=c, fontweight="bold")
ax.set_xticks([2026, 2027, 2028, 2029]); ax.set_ylabel("Long-term debt ÷ equity"); ax.set_xlim(2025.8, 2029.5)
ax.legend(frameon=False, loc="upper left")
title(ax, "At 30% growth, debt reaches 2.2x equity in three years",
      "Illustrative percent-of-sales projection: 2026 margins and asset intensity held, debt as the plug")
fig.savefig(OUT / "05_projection.png"); plt.close(fig)

results = {
    "ratios": {y: {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r[y].items()} for y in Y},
    "trade_credit_2025": {k: round(v, 4) for k, v in m.trade_credit(d).items()},
    "funding_2026": f,
    "projection_2029_debt_to_equity": {lab: round(p[-1]["debt_to_equity"], 3) for lab, p, *_ in paths},
}
(ROOT / "results.json").write_text(json.dumps(results, indent=2))
print("charts and results.json written")
