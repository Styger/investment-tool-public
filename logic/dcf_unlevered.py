# logic/dcf_unlevered.py

import api.fmp_api as fmp


def _to_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default


def _find_year(lst, year):
    """Return dict for exact calendarYear==year (string compare)."""
    if not isinstance(lst, list):
        return {}
    y = str(year)
    for row in lst:
        if str(row.get("calendarYear")) == y:
            return row
    return {}


def _latest(lst):
    if isinstance(lst, list) and lst:
        return lst[0]
    return lst or {}


def _calc_fcff(ebit, tax_rate, depreciation, capex, delta_nwc):
    ebit_after_tax = ebit * (1.0 - max(0.0, min(tax_rate, 0.6)))
    return ebit_after_tax + depreciation - capex - delta_nwc


def _discount_series(cashflows, rate, mid_year=True):
    pv = 0.0
    out = []
    for t, cf in enumerate(cashflows, start=1):
        expo = (t - 0.5) if mid_year else t
        val = cf / ((1.0 + rate) ** expo)
        out.append(val)
        pv += val
    return pv, out


def _terminal_value_gordon(last_fcff, wacc, perp_growth):
    g = perp_growth
    if wacc <= g:
        return None
    return last_fcff * (1.0 + g) / (wacc - g)


# -----------------------------
# Data collection
# -----------------------------


def _fetch_financials(ticker, base_year=None):
    """
    Pull a specific calendarYear (if base_year given) or the latest.
    Returns a dict with all building blocks. Raises ValueError if base_year not found.
    """
    inc_all = fmp.get_income_statement(ticker, limit=30) or []
    cfs_all = fmp.get_cashflow_statement(ticker, limit=30) or []
    bal_all = fmp.get_balance_sheet(ticker, limit=30) or []
    met_all = fmp.get_key_metrics(ticker, limit=30) or []

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

    # Currency: prefer statement currencies, then metrics, then USD
    currency = (
        inc.get("reportedCurrency")
        or cfs.get("reportedCurrency")
        or bal.get("reportedCurrency")
        or met.get("currency")
        or "USD"
    )

    data = {
        "EBIT": _to_float(inc.get("ebit")) or _to_float(inc.get("operatingIncome")),
        "taxRate": (
            _to_float(inc.get("incomeTaxExpense"))
            / max(1.0, _to_float(inc.get("incomeBeforeTax")))
            if _to_float(inc.get("incomeBeforeTax"))
            else None
        ),
        "depreciation": _to_float(
            cfs.get("depreciationAndAmortization")
            or cfs.get("depreciation")
            or cfs.get("depreciationAmortizationDepletion")
            or cfs.get("depreciationDepletionAndAmortization")
        ),
        "capex": abs(_to_float(cfs.get("capitalExpenditure"))),
        "delta_nwc": _to_float(cfs.get("changeInWorkingCapital")),
        "total_debt": _to_float(bal.get("totalDebt") or 0.0),
        "cash": _to_float(bal.get("cashAndCashEquivalents") or 0.0),
        "shares": _to_float(
            met.get("weightedAverageShsOutDil")
            or met.get("weightedAverageShsOut")
            or inc.get("weightedAverageShsOutDil")
            or inc.get("weightedAverageShsOut")
            or 0.0
        ),
        "asOf": inc.get("date")
        or cfs.get("date")
        or bal.get("date")
        or met.get("date"),
        "currency": currency,
        "base_year": base_year if base_year is not None else inc.get("calendarYear"),
    }

    if data["taxRate"] is not None:
        data["taxRate"] = max(0.0, min(data["taxRate"], 0.6))

    return data


# -----------------------------
# Core API
# -----------------------------


def dcf_unlevered(
    ticker,
    forecast_years=5,
    fcff_growth=0.08,
    perp_growth=0.03,
    wacc=0.10,
    tax_rate=None,
    mid_year=True,
    shares_override=None,
    base_year=None,  # <-- NEW: compute “as of” this fiscal year
):
    base = _fetch_financials(ticker, base_year=base_year)
    if base.get("EBIT") is None:
        base["EBIT"] = 0.0

    tr = (
        tax_rate
        if tax_rate is not None
        else (base.get("taxRate") if base.get("taxRate") is not None else 0.21)
    )

    fcff0 = _calc_fcff(
        ebit=base["EBIT"],
        tax_rate=tr,
        depreciation=base["depreciation"],
        capex=base["capex"],
        delta_nwc=base["delta_nwc"],
    )

    fcffs = []
    current = fcff0
    for _ in range(forecast_years):
        current *= 1.0 + fcff_growth
        fcffs.append(current)

    pv_explicit, pv_each = _discount_series(fcffs, wacc, mid_year=mid_year)

    tv = _terminal_value_gordon(fcffs[-1] if fcffs else fcff0, wacc, perp_growth)
    if tv is None:
        pv_tv = None
        ev = pv_explicit
    else:
        expo = (forecast_years - 0.5) if mid_year else forecast_years
        pv_tv = tv / ((1.0 + wacc) ** expo)
        ev = pv_explicit + pv_tv

    net_debt = base["total_debt"] - base["cash"]
    equity_value = ev - net_debt

    shares = shares_override if shares_override else (base.get("shares") or 0.0)
    fair_value_per_share = (equity_value / shares) if shares > 0 else None

    return {
        "ticker": ticker.upper(),
        "as_of": base.get("asOf"),
        "base_year": base.get("base_year"),
        "currency": base.get("currency", "USD"),
        "wacc": wacc,
        "fcff_growth": fcff_growth,
        "perp_growth": perp_growth,
        "tax_rate_used": tr,
        "forecast_years": forecast_years,
        "mid_year": bool(mid_year),
        "EBIT": base["EBIT"],
        "depreciation": base["depreciation"],
        "capex": base["capex"],
        "delta_nwc": base["delta_nwc"],
        "fcff0": fcff0,
        "fcff_years": fcffs,
        "pv_fcff_years": pv_each,
        "pv_explicit": pv_explicit,
        "terminal_value": tv,
        "pv_terminal": pv_tv,
        "enterprise_value": ev,
        "total_debt": base["total_debt"],
        "cash": base["cash"],
        "net_debt": net_debt,
        "equity_value": equity_value,
        "shares": shares,
        "fair_value_per_share": fair_value_per_share,
    }


def _print_dcf_unlevered(
    ticker,
    forecast_years=5,
    fcff_growth=0.08,
    perp_growth=0.03,
    wacc=0.10,
    tax_rate=None,
    mid_year=True,
    shares_override=None,
    mos_percent=0.5,
    base_year=None,  # <-- NEW
):
    r = dcf_unlevered(
        ticker=ticker,
        forecast_years=forecast_years,
        fcff_growth=fcff_growth,
        perp_growth=perp_growth,
        wacc=wacc,
        tax_rate=tax_rate,
        mid_year=mid_year,
        shares_override=shares_override,
        base_year=base_year,
    )

    print(
        f"\n==== {r['ticker']} Unlevered DCF (base year {r.get('base_year')}, as of {r.get('as_of') or 'N/A'}) ====\n"
    )
    print(f"Currency:               {r['currency']}")
    print(f"Base FCFF (t=0):        {r['fcff0']:,.0f} {r['currency']}")
    print(
        f"WACC:                   {r['wacc'] * 100:.2f}%   |  Growth (N): {r['fcff_growth'] * 100:.2f}%   |  g (perp): {r['perp_growth'] * 100:.2f}%"
    )
    print(f"Mid-year adjustment:    {r['mid_year']}")
    print(f"Forecast years:         {r['forecast_years']}\n")

    for i, (fcff, pv) in enumerate(zip(r["fcff_years"], r["pv_fcff_years"]), start=1):
        print(f" Year {i}: FCFF={fcff:,.0f}   PV={pv:,.0f}")

    print()
    print(f"PV explicit FCFF:       {r['pv_explicit']:,.0f} {r['currency']}")
    if r["pv_terminal"] is not None:
        print(f"Terminal Value:         {r['terminal_value']:,.0f} {r['currency']}")
        print(f"PV Terminal:            {r['pv_terminal']:,.0f} {r['currency']}")
    print(f"Enterprise Value (EV):  {r['enterprise_value']:,.0f} {r['currency']}")
    print(f"Net Debt:               {r['net_debt']:,.0f} {r['currency']}")
    print(f"Equity Value:           {r['equity_value']:,.0f} {r['currency']}")
    if r["shares"] > 0 and r["fair_value_per_share"] is not None:
        fv = r["fair_value_per_share"]
        print(f"Shares (diluted):       {r['shares']:,.0f}")
        print(f"Fair Value / Share:     {fv:,.2f} {r['currency']}")
        if mos_percent is not None:
            buy = fv * (1.0 - mos_percent)
            print(
                f"MOS ({int(mos_percent * 100)}%) Buy Price: {buy:,.2f} {r['currency']}"
            )
    print()


if __name__ == "__main__":
    _print_dcf_unlevered(
        ticker="AAPL",
        forecast_years=5,
        fcff_growth=0.08,
        perp_growth=0.03,
        wacc=0.10,
        tax_rate=None,
        mid_year=True,
        shares_override=None,
        mos_percent=0.5,
        base_year=2024,  # <--- setze None für "letztes verfügbares Jahr"
    )
