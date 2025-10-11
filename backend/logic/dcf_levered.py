# logic/dcf_levered.py
"""
Levered DCF (FCFE) valuation using FMP fundamental data.

FCFE (Equity cash flow) – zwei gängige Näherungen:
A) FCFE ≈ CFO - CapEx + Net Borrowing
B) FCFE ≈ Net Income + D&A - CapEx - ΔNWC + Net Borrowing

Wir verwenden A), weil CFO (Operating Cash Flow) ΔNWC & Cash-Steuern schon enthält
und auf FMP stabil verfügbar ist. Net Borrowing schätzen wir als
(debtIssuance - debtRepayment), falls vorhanden; sonst 0.

Diskontierung mit Cost of Equity (ke), Terminalwert via Gordon Growth.
Equity Value = PV(FCFE explizit) + PV(Terminal).
Fair Value je Aktie = Equity Value / (verwässerte) Aktien.

Optional: base_year für DCF „aus Sicht eines bestimmten Jahres".
"""

# import api.fmp_api as fmp
import sys
from pathlib import Path

# Stelle sicher, dass das Root-Verzeichnis im Python-Path ist
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.api import fmp_api


# ------------- Helpers -------------


def _to_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default


def _latest(lst):
    if isinstance(lst, list) and lst:
        return lst[0]
    return lst or {}


def _find_year(lst, year):
    if not isinstance(lst, list):
        return {}
    y = str(year)
    for row in lst:
        if str(row.get("calendarYear")) == y:
            return row
    return {}


def _discount_series(cashflows, rate, mid_year=True):
    pv = 0.0
    out = []
    for t, cf in enumerate(cashflows, start=1):
        expo = (t - 0.5) if mid_year else t
        val = cf / ((1.0 + rate) ** expo)
        out.append(val)
        pv += val
    return pv, out


def _terminal_value_gordon(last_cf, ke, perp_growth):
    g = perp_growth
    if ke <= g:
        return None
    return last_cf * (1.0 + g) / (ke - g)


def _get_investment_recommendation(current_price, fair_value, buy_price):
    """Gibt eine Investitionsempfehlung basierend auf den Preisvergleichen."""
    if current_price is None or current_price <= 0:
        return "No price data available"

    if current_price <= buy_price:
        return "Strong Buy (Below MOS price)"
    elif current_price <= fair_value:
        return "Buy (Below fair value)"
    elif current_price <= fair_value * 1.1:
        return "Hold (Near fair value)"
    else:
        return "Avoid (Overvalued)"


# ------------- Data collection -------------


def _fetch_financials_fcfe(ticker, base_year=None):
    """
    Holt Income/Cashflow/Balance/Metrics für base_year (falls angegeben) oder das neueste Jahr.
    Liefert die Bausteine für FCFE & Bewertung. Wir verwenden primär das Cashflow-Statement.
    """
    inc_all = fmp_api.get_income_statement(ticker, limit=30) or []
    cfs_all = fmp_api.get_cashflow_statement(ticker, limit=30) or []
    bal_all = fmp_api.get_balance_sheet(ticker, limit=30) or []
    met_all = fmp_api.get_key_metrics(ticker, limit=30) or []

    if base_year is None:
        inc = _latest(inc_all)
        cfs = _latest(cfs_all)
        bal = _latest(bal_all)
        met = _latest(met_all)
    else:
        inc = _find_year(inc_all, base_year)
        cfs = _find_year(cfs_all, base_year)
        bal = _find_year(bal_all, base_year)
        met = _find_year(met_all, base_year)
        if not (inc and cfs and bal):
            raise ValueError(f"No complete statements found for year {base_year}.")

    # Currency robust bestimmen
    currency = (
        inc.get("reportedCurrency")
        or cfs.get("reportedCurrency")
        or bal.get("reportedCurrency")
        or met.get("currency")
        or "USD"
    )

    # Operating Cash Flow (CFO)
    cfo = _to_float(
        cfs.get("netCashProvidedByOperatingActivities")
        or cfs.get("operatingCashFlow")
        or cfs.get("netCashProvidedByOperatingActivitiesIndirect")
    )

    # CapEx (meist negativ in Quelle -> als positiver Abfluss behandeln)
    capex = abs(_to_float(cfs.get("capitalExpenditure")))

    # Net Borrowing (Nettoverschuldung neu aufgenommen): Issuance - Repayment
    net_borrowing = _to_float(cfs.get("debtIssuance")) - _to_float(
        cfs.get("debtRepayment")
    )

    # Aktien (verwässert, wo verfügbar)
    shares = _to_float(
        met.get("weightedAverageShsOutDil")
        or met.get("weightedAverageShsOut")
        or inc.get("weightedAverageShsOutDil")
        or inc.get("weightedAverageShsOut")
        or 0.0
    )

    data = {
        "cfo": cfo,
        "capex": capex,
        "net_borrowing": net_borrowing,
        "shares": shares,
        "asOf": inc.get("date")
        or cfs.get("date")
        or bal.get("date")
        or met.get("date"),
        "currency": currency,
        "base_year": base_year if base_year is not None else inc.get("calendarYear"),
    }
    return data


# ------------- Core API -------------


def dcf_levered(
    ticker,
    forecast_years=5,
    fcfe_growth=0.08,  # Wachstum der FCFE in der Explizitphase
    perp_growth=0.03,  # Terminalwachstum
    cost_of_equity=0.11,  # Diskontierung (Ke)
    mid_year=True,
    shares_override=None,
    base_year=None,  # DCF „aus Sicht" eines bestimmten Jahres
    mos_percent=0.25,  # NEW: MOS parameter
):
    """
    FCFE-basierte (levered) DCF.
    FCFE_0 ≈ CFO - CapEx + NetBorrowing
    Equity Value = PV(FCFE explizit) + PV(Terminal)
    """
    base = _fetch_financials_fcfe(ticker, base_year=base_year)

    fcfe0 = base["cfo"] - base["capex"] + base["net_borrowing"]

    # Projektion
    fcfes = []
    current = fcfe0
    for _ in range(forecast_years):
        current *= 1.0 + fcfe_growth
        fcfes.append(current)

    # Diskontierung
    pv_explicit, pv_each = _discount_series(fcfes, cost_of_equity, mid_year=mid_year)

    # Terminal
    tv = _terminal_value_gordon(
        fcfes[-1] if fcfes else fcfe0, cost_of_equity, perp_growth
    )
    if tv is None:
        pv_tv = None
        equity_value = pv_explicit
    else:
        expo = (forecast_years - 0.5) if mid_year else forecast_years
        pv_tv = tv / ((1.0 + cost_of_equity) ** expo)
        equity_value = pv_explicit + pv_tv

    # Fair Value je Aktie
    shares = shares_override if shares_override else (base.get("shares") or 0.0)
    fair_value_per_share = (equity_value / shares) if shares > 0 else None

    # NEW: Calculate buy price with MOS
    buy_price_per_share = (
        (fair_value_per_share * (1 - mos_percent)) if fair_value_per_share else None
    )

    # NEW: Get current stock price and calculate comparisons
    current_price = None
    price_vs_fair = None
    price_vs_buy = None
    investment_recommendation = None

    try:
        current_price = fmp_api.get_current_price(ticker)

        if current_price and fair_value_per_share:
            # Fair Value Vergleich
            fair_ratio = (current_price / fair_value_per_share - 1) * 100
            if fair_ratio > 0:
                price_vs_fair = f"Overvalued by {fair_ratio:.1f}%"
            else:
                price_vs_fair = f"Undervalued by {abs(fair_ratio):.1f}%"

            # Buy Price Vergleich
            if buy_price_per_share:
                buy_ratio = (current_price / buy_price_per_share - 1) * 100
                if buy_ratio > 0:
                    price_vs_buy = f"Above buy price by {buy_ratio:.1f}%"
                else:
                    price_vs_buy = f"Below buy price by {abs(buy_ratio):.1f}%"

            # Investment Empfehlung
            investment_recommendation = _get_investment_recommendation(
                current_price, fair_value_per_share, buy_price_per_share
            )

    except Exception as e:
        print(f"Could not fetch current price for {ticker}: {e}")

    return {
        "ticker": ticker.upper(),
        "as_of": base.get("asOf"),
        "base_year": base.get("base_year"),
        "currency": base.get("currency", "USD"),
        # Annahmen
        "cost_of_equity": cost_of_equity,
        "fcfe_growth": fcfe_growth,
        "perp_growth": perp_growth,
        "forecast_years": forecast_years,
        "mid_year": bool(mid_year),
        "mos_percent": mos_percent,  # NEW
        # Bausteine
        "fcfe0": fcfe0,
        "cfo": base["cfo"],
        "capex": base["capex"],
        "net_borrowing": base["net_borrowing"],
        # PVs
        "fcfe_years": fcfes,
        "pv_fcfe_years": pv_each,
        "pv_explicit": pv_explicit,
        "terminal_value": tv,
        "pv_terminal": pv_tv,
        # Equity
        "equity_value": equity_value,
        "shares": shares,
        "fair_value_per_share": fair_value_per_share,
        "buy_price_per_share": buy_price_per_share,  # NEW
        "current_stock_price": current_price,  # NEW
        "price_vs_fair": price_vs_fair,  # NEW
        "price_vs_buy": price_vs_buy,  # NEW
        "investment_recommendation": investment_recommendation,  # NEW
    }


def _print_dcf_levered(
    ticker,
    forecast_years=5,
    fcfe_growth=0.08,
    perp_growth=0.03,
    cost_of_equity=0.11,
    mid_year=True,
    shares_override=None,
    mos_percent=0.25,
    base_year=None,
):
    r = dcf_levered(
        ticker=ticker,
        forecast_years=forecast_years,
        fcfe_growth=fcfe_growth,
        perp_growth=perp_growth,
        cost_of_equity=cost_of_equity,
        mid_year=mid_year,
        shares_override=shares_override,
        base_year=base_year,
        mos_percent=mos_percent,
    )

    print(
        f"\n==== {r['ticker']} Levered DCF (FCFE) — base year {r.get('base_year')}, as of {r.get('as_of') or 'N/A'} ====\n"
    )
    print(f"Currency:               {r['currency']}")
    print(f"FCFE base (t=0):        {r['fcfe0']:,.0f} {r['currency']}")
    print(
        f"Ke:                     {r['cost_of_equity'] * 100:.2f}%   |  Growth (N): {r['fcfe_growth'] * 100:.2f}%   |  g (perp): {r['perp_growth'] * 100:.2f}%"
    )
    print(f"Mid-year adjustment:    {r['mid_year']}")
    print(f"Forecast years:         {r['forecast_years']}\n")

    for i, (cf, pv) in enumerate(zip(r["fcfe_years"], r["pv_fcfe_years"]), start=1):
        print(f" Year {i}: FCFE={cf:,.0f}   PV={pv:,.0f}")

    print()
    print(f"PV explicit FCFE:       {r['pv_explicit']:,.0f} {r['currency']}")
    if r["pv_terminal"] is not None:
        print(f"Terminal Value:         {r['terminal_value']:,.0f} {r['currency']}")
        print(f"PV Terminal:            {r['pv_terminal']:,.0f} {r['currency']}")
    print(f"Equity Value:           {r['equity_value']:,.0f} {r['currency']}")

    if r["shares"] > 0 and r["fair_value_per_share"] is not None:
        fv = r["fair_value_per_share"]
        buy = r["buy_price_per_share"]
        print(f"Shares (diluted):       {r['shares']:,.0f}")
        print(f"Fair Value / Share:     {fv:,.2f} {r['currency']}")
        print(
            f"Buy Price ({int(r['mos_percent'] * 100)}% MOS): {buy:,.2f} {r['currency']}"
        )

        if r["current_stock_price"]:
            print(
                f"Current Stock Price:    {r['current_stock_price']:,.2f} {r['currency']}"
            )
            if r["price_vs_fair"]:
                print(f"vs Fair Value:          {r['price_vs_fair']}")
            if r["price_vs_buy"]:
                print(f"vs Buy Price:           {r['price_vs_buy']}")
            if r["investment_recommendation"]:
                print(f"Recommendation:         {r['investment_recommendation']}")
    print()


if __name__ == "__main__":
    # Schnelltest: Basisjahr explizit oder None für "letztes verfügbares Jahr"
    _print_dcf_levered(
        ticker="AAPL",
        forecast_years=5,
        fcfe_growth=0.08,
        perp_growth=0.03,
        cost_of_equity=0.11,
        mid_year=True,
        shares_override=None,
        mos_percent=0.25,
        base_year=2023,  # oder None
    )
