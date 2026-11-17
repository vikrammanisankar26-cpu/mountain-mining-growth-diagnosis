"""Mountain Mining Co.: is the company growing faster than it can afford?

Ratio analysis, DuPont, sustainable growth (Higgins), working-capital days,
the cost of forgoing supplier discounts, and a percent-of-sales projection.
Data: data/mountain_mining.csv (course case, US$).
"""
import csv
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "mountain_mining.csv"
YEARS = ["2024", "2025", "2026"]


def load(path=DATA):
    with open(path, newline="") as f:
        d = {r["line_item"]: {y: float(r[y]) for y in YEARS} for r in csv.DictReader(f)}
    for y in YEARS:
        g = lambda k: d[k][y]  # noqa: E731
        ebit = g("sales") - g("cogs") - g("depreciation") - g("sga") - g("other_operating")
        ni = (ebit - g("interest")) * (1 - g("tax_rate"))
        cur = g("cash") + g("marketable_securities") + g("accounts_receivable") + g("inventory")
        assets = cur + g("gross_ppe") - g("accumulated_depreciation")
        equity = g("common_stock") + g("paid_in_capital") + g("retained_earnings")
        for k, v in dict(ebit=ebit, net_income=ni, current_assets=cur, total_assets=assets, equity=equity,
                         current_liabilities=g("accounts_payable") + g("accrued_expenses")).items():
            d.setdefault(k, {})[y] = v
    return d


def ratios(d):
    out = {}
    for i, y in enumerate(YEARS):
        g = lambda k, yy=y: d[k][yy]  # noqa: E731
        r = {
            "sales_growth": None if i == 0 else g("sales") / d["sales"][YEARS[i - 1]] - 1,
            "gross_margin": (g("sales") - g("cogs")) / g("sales"),
            "ebit_margin": g("ebit") / g("sales"),
            "net_margin": g("net_income") / g("sales"),
            "current_ratio": g("current_assets") / g("current_liabilities"),
            "quick_ratio": (g("current_assets") - g("inventory")) / g("current_liabilities"),
            "debt_to_equity": g("long_term_debt") / g("equity"),
            "debt_to_assets": g("long_term_debt") / g("total_assets"),
            "interest_coverage": g("ebit") / g("interest"),
            "dso": g("accounts_receivable") / g("sales") * 365,
            "dio": g("inventory") / g("cogs") * 365,
            "dpo": g("accounts_payable") / g("cogs") * 365,
            "asset_turnover_end": g("sales") / g("total_assets"),
        }
        r["cash_conversion_cycle"] = r["dso"] + r["dio"] - r["dpo"]
        if i > 0:
            p = YEARS[i - 1]
            dividends = g("net_income") - (g("retained_earnings") - d["retained_earnings"][p])
            beg_eq, beg_assets = d["equity"][p], d["total_assets"][p]
            r.update({
                "dividends": dividends,
                "payout": dividends / g("net_income"),
                "retention": 1 - dividends / g("net_income"),
                "roe_beginning": g("net_income") / beg_eq,
                # DuPont on beginning-of-year balances (Higgins)
                "asset_turnover": g("sales") / beg_assets,
                "equity_multiplier": beg_assets / beg_eq,
            })
            r["sustainable_growth"] = r["roe_beginning"] * r["retention"]
        out[y] = r
    return out


def trade_credit(d, year="2025", discount=0.02, disc_days=30, net_days=60):
    """Cost of paying on day 60 instead of taking a 2% discount on day 30."""
    p = YEARS[YEARS.index(year) - 1]
    purchases = d["cogs"][year] + (d["inventory"][year] - d["inventory"][p])
    per_period = discount / (1 - discount)
    periods = 365 / (net_days - disc_days)
    t = d["tax_rate"][year]
    avg_debt = (d["long_term_debt"][year] + d["long_term_debt"][p]) / 2
    effective = (1 + per_period) ** periods - 1
    return {
        "purchases": purchases,
        "nominal_cost": per_period * periods,
        "effective_cost": effective,
        "effective_cost_after_tax": effective * (1 - t),
        "discounts_forgone": discount * purchases,
        "discounts_share_of_net_income": discount * purchases / d["net_income"][year],
        "cost_of_debt": d["interest"][year] / avg_debt,
    }


def funding(d, year="2026"):
    """Where the money for this year's asset growth came from."""
    p = YEARS[YEARS.index(year) - 1]
    delta = lambda k: d[k][year] - d[k][p]  # noqa: E731
    return {
        "asset_growth": delta("total_assets"),
        "retained_earnings": delta("retained_earnings"),
        "new_debt": delta("long_term_debt"),
        "payables_and_accruals": delta("accounts_payable") + delta("accrued_expenses"),
        "new_equity": delta("common_stock") + delta("paid_in_capital"),
    }


def project(d, growth, years=3, payout=None):
    """Percent-of-sales projection from 2026: assets and spontaneous liabilities scale with
    sales, margins and payout stay at 2026 levels, debt is the plug. Illustrative only."""
    r26 = ratios(d)["2026"]
    s0 = d["sales"]["2026"]
    assets_pct = d["total_assets"]["2026"] / s0
    spont_pct = d["current_liabilities"]["2026"] / s0
    margin, pay = r26["net_margin"], (r26["payout"] if payout is None else payout)
    # Interest is charged on opening debt: 2026 interest / 2025 closing debt reproduces 2026 exactly.
    rate = d["interest"]["2026"] / d["long_term_debt"]["2025"]
    ebit_margin = r26["ebit_margin"]
    sales, equity, debt = s0, d["equity"]["2026"], d["long_term_debt"]["2026"]
    path = [{"year": 2026, "sales": sales, "debt": debt, "debt_to_equity": debt / equity,
             "interest_coverage": r26["interest_coverage"]}]
    for k in range(1, years + 1):
        opening_debt = debt
        sales *= 1 + growth
        equity += sales * margin * (1 - pay)
        debt = sales * assets_pct - sales * spont_pct - equity
        path.append({"year": 2026 + k, "sales": sales, "debt": debt, "debt_to_equity": debt / equity,
                     "interest_coverage": sales * ebit_margin / (opening_debt * rate)})
    return path
