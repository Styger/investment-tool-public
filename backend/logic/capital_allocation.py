from typing import Dict, List, Optional
import sys
from pathlib import Path

# Stelle sicher, dass das Root-Verzeichnis im Python-Path ist
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.api import fmp_api


def calculate_capital_allocation_from_ticker(ticker: str, year: int) -> Dict:
    """
    Calculates capital allocation metrics for a company for a single year.
    Shows how the company uses its Free Cash Flow.

    Args:
        ticker: Stock symbol
        year: Year for analysis

    Returns:
        Dict with capital allocation metrics (absolute values and percentages)
    """
    # Fetch Cash Flow Statement, Balance Sheet, and Key Metrics
    cashflow_statement = fmp_api.get_cashflow_statement(ticker, limit=20)
    balance_sheet = fmp_api.get_balance_sheet(ticker, limit=20)
    key_metrics = fmp_api.get_key_metrics(ticker, limit=20)

    # Find data for the specified year
    def get_by_year(data, target_year):
        for entry in data:
            if str(entry.get("calendarYear")) == str(target_year):
                return entry
        return {}

    cf_data = get_by_year(cashflow_statement, year)
    bs_data_current = get_by_year(balance_sheet, year)
    bs_data_previous = get_by_year(balance_sheet, year - 1)
    km_data = get_by_year(key_metrics, year)

    # Extract Cash Flow Statement values
    fcf = cf_data.get("freeCashFlow", 0)

    # If FCF is not directly available, calculate it
    if fcf == 0:
        operating_cf = cf_data.get("operatingCashFlow", 0)
        capex = cf_data.get("capitalExpenditure", 0)
        fcf = operating_cf + capex  # capex is usually negative

    # Extract absolute values (convert to positive)
    dividends_paid = abs(cf_data.get("dividendsPaid", 0))
    stock_buybacks = abs(cf_data.get("commonStockRepurchased", 0))
    debt_repayment = abs(cf_data.get("debtRepayment", 0))
    capex = abs(cf_data.get("capitalExpenditure", 0))
    acquisitions = abs(cf_data.get("acquisitionsNet", 0))

    # Calculate cash increase from Balance Sheet
    cash_current = bs_data_current.get("cashAndCashEquivalents", 0)
    cash_previous = bs_data_previous.get("cashAndCashEquivalents", 0)
    cash_increase = cash_current - cash_previous

    # Extract shares outstanding and total debt for ratios
    shares_outstanding = km_data.get("numberOfShares", 0)
    if shares_outstanding == 0:
        # Fallback: try weightedAverageShsOut from income statement or commonStock from balance sheet
        shares_outstanding = bs_data_current.get("commonStock", 0)

    total_debt = bs_data_current.get("totalDebt", 0)

    # Calculate "Other" - what's left after all known uses
    total_uses = (
        dividends_paid
        + stock_buybacks
        + debt_repayment
        + capex
        + acquisitions
        + max(0, cash_increase)
    )
    other = max(0, fcf - total_uses) if fcf > 0 else 0

    # Calculate percentages (only if FCF is positive)
    if fcf > 0:
        dividends_pct = (dividends_paid / fcf) * 100
        buybacks_pct = (stock_buybacks / fcf) * 100
        debt_repayment_pct = (debt_repayment / fcf) * 100
        capex_pct = (capex / fcf) * 100
        acquisitions_pct = (acquisitions / fcf) * 100
        cash_increase_pct = (max(0, cash_increase) / fcf) * 100
        other_pct = (other / fcf) * 100
    else:
        # If FCF is negative or zero, percentages don't make sense
        dividends_pct = None
        buybacks_pct = None
        debt_repayment_pct = None
        capex_pct = None
        acquisitions_pct = None
        cash_increase_pct = None
        other_pct = None

    # Calculate ratios (per share and debt-related)
    dividends_per_share = (
        dividends_paid / shares_outstanding if shares_outstanding > 0 else None
    )
    buybacks_per_share = (
        stock_buybacks / shares_outstanding if shares_outstanding > 0 else None
    )
    debt_repayment_pct_of_total = (
        (debt_repayment / total_debt) * 100 if total_debt > 0 else None
    )

    # Return pure data
    result = {
        "ticker": ticker.upper(),
        "year": year,
        "fcf": fcf,
        # Absolute values
        "dividends_paid": dividends_paid,
        "stock_buybacks": stock_buybacks,
        "debt_repayment": debt_repayment,
        "capex": capex,
        "acquisitions": acquisitions,
        "cash_increase": max(0, cash_increase),
        "other": other,
        # Percentage allocation (% of FCF)
        "dividends_pct": dividends_pct,
        "buybacks_pct": buybacks_pct,
        "debt_repayment_pct": debt_repayment_pct,
        "capex_pct": capex_pct,
        "acquisitions_pct": acquisitions_pct,
        "cash_increase_pct": cash_increase_pct,
        "other_pct": other_pct,
        # Additional context data
        "shares_outstanding": shares_outstanding,
        "total_debt": total_debt,
        # Ratios
        "dividends_per_share": dividends_per_share,
        "buybacks_per_share": buybacks_per_share,
        "debt_repayment_pct_of_total": debt_repayment_pct_of_total,
    }

    print(f"Capital Allocation Analysis Result: {result}")
    return result


def calculate_capital_allocation_multi_year(
    ticker: str, start_year: int, end_year: int
) -> List[Dict]:
    """
    Calculates capital allocation metrics for a company across multiple years.

    Args:
        ticker: Stock symbol
        start_year: Starting year
        end_year: Ending year

    Returns:
        List of dicts with capital allocation metrics for each year
    """
    results = []

    for year in range(start_year, end_year + 1):
        result = calculate_capital_allocation_from_ticker(ticker, year)
        results.append(result)

    print(
        f"Capital Allocation Analysis for {ticker} from {start_year} to {end_year}: {len(results)} years"
    )
    return results


if __name__ == "__main__":
    ticker = "AAPL"
    year = 2024

    print("\n" + "=" * 80)
    print("=== Single Year Capital Allocation Analysis ===")
    print("=" * 80)
    result = calculate_capital_allocation_from_ticker(ticker, year)

    print(f"\n{'COMPANY:':<30} {ticker}")
    print(f"{'YEAR:':<30} {year}")
    print(f"{'FREE CASH FLOW:':<30} ${result['fcf'] / 1_000_000:,.2f}M")
    print(
        f"{'SHARES OUTSTANDING:':<30} {result['shares_outstanding'] / 1_000_000:,.2f}M shares"
    )
    print(f"{'TOTAL DEBT:':<30} ${result['total_debt'] / 1_000_000:,.2f}M")

    print("\n" + "-" * 80)
    print("USES OF FREE CASH FLOW")
    print("-" * 80)

    # Dividends
    div_abs = f"${result['dividends_paid'] / 1_000_000:,.2f}M"
    div_pct = (
        f"({result['dividends_pct']:.1f}% of FCF)"
        if result["dividends_pct"]
        else "(N/A)"
    )
    div_per_share = (
        f"${result['dividends_per_share']:.2f}/share"
        if result["dividends_per_share"]
        else "N/A"
    )
    print(f"  💵 Dividends:        {div_abs:<15} {div_pct:<18} [{div_per_share}]")

    # Buybacks
    buy_abs = f"${result['stock_buybacks'] / 1_000_000:,.2f}M"
    buy_pct = (
        f"({result['buybacks_pct']:.1f}% of FCF)" if result["buybacks_pct"] else "(N/A)"
    )
    buy_per_share = (
        f"${result['buybacks_per_share']:.2f}/share"
        if result["buybacks_per_share"]
        else "N/A"
    )
    print(f"  🔄 Buybacks:         {buy_abs:<15} {buy_pct:<18} [{buy_per_share}]")

    # Debt Repayment
    debt_abs = f"${result['debt_repayment'] / 1_000_000:,.2f}M"
    debt_pct = (
        f"({result['debt_repayment_pct']:.1f}% of FCF)"
        if result["debt_repayment_pct"]
        else "(N/A)"
    )
    debt_of_total = (
        f"{result['debt_repayment_pct_of_total']:.1f}% of total debt"
        if result["debt_repayment_pct_of_total"]
        else "N/A"
    )
    print(f"  💳 Debt Repayment:   {debt_abs:<15} {debt_pct:<18} [{debt_of_total}]")

    # Capex
    capex_abs = f"${result['capex'] / 1_000_000:,.2f}M"
    capex_pct = (
        f"({result['capex_pct']:.1f}% of FCF)" if result["capex_pct"] else "(N/A)"
    )
    print(f"  🏗️  Capex:            {capex_abs:<15} {capex_pct:<18}")

    # M&A
    ma_abs = f"${result['acquisitions'] / 1_000_000:,.2f}M"
    ma_pct = (
        f"({result['acquisitions_pct']:.1f}% of FCF)"
        if result["acquisitions_pct"]
        else "(N/A)"
    )
    print(f"  🤝 M&A:              {ma_abs:<15} {ma_pct:<18}")

    # Cash Increase
    cash_abs = f"${result['cash_increase'] / 1_000_000:,.2f}M"
    cash_pct = (
        f"({result['cash_increase_pct']:.1f}% of FCF)"
        if result["cash_increase_pct"]
        else "(N/A)"
    )
    print(f"  💰 Cash Increase:    {cash_abs:<15} {cash_pct:<18}")

    # Other
    other_abs = f"${result['other'] / 1_000_000:,.2f}M"
    other_pct = (
        f"({result['other_pct']:.1f}% of FCF)" if result["other_pct"] else "(N/A)"
    )
    print(f"  📦 Other:            {other_abs:<15} {other_pct:<18}")

    print("\n" + "=" * 80)
    print("=== Multi-Year Capital Allocation Analysis ===")
    print("=" * 80)
    results = calculate_capital_allocation_multi_year(ticker, 2022, 2024)

    # Header
    print(
        f"\n{'Year':<6} {'FCF':<15} {'Dividends':<25} {'Buybacks':<25} {'Debt Repay':<25}"
    )
    print(
        f"{'':6} {'':15} {'(% FCF | $/share)':<25} {'(% FCF | $/share)':<25} {'(% FCF | % debt)':<25}"
    )
    print("-" * 100)

    for r in results:
        # Format values
        fcf_str = f"${r['fcf'] / 1_000_000:,.0f}M"

        # Dividends with per-share ratio
        div_abs = f"${r['dividends_paid'] / 1_000_000:,.0f}M"
        div_pct = f"{r['dividends_pct']:.1f}%" if r["dividends_pct"] else "N/A"
        div_per_share = (
            f"${r['dividends_per_share']:.2f}" if r["dividends_per_share"] else "N/A"
        )
        div_str = f"{div_abs} ({div_pct} | {div_per_share}/sh)"

        # Buybacks with per-share ratio
        buy_abs = f"${r['stock_buybacks'] / 1_000_000:,.0f}M"
        buy_pct = f"{r['buybacks_pct']:.1f}%" if r["buybacks_pct"] else "N/A"
        buy_per_share = (
            f"${r['buybacks_per_share']:.2f}" if r["buybacks_per_share"] else "N/A"
        )
        buy_str = f"{buy_abs} ({buy_pct} | {buy_per_share}/sh)"

        # Debt Repayment with % of total debt
        debt_abs = f"${r['debt_repayment'] / 1_000_000:,.0f}M"
        debt_fcf_pct = (
            f"{r['debt_repayment_pct']:.1f}%" if r["debt_repayment_pct"] else "N/A"
        )
        debt_total_pct = (
            f"{r['debt_repayment_pct_of_total']:.1f}%"
            if r["debt_repayment_pct_of_total"]
            else "N/A"
        )
        debt_str = f"{debt_abs} ({debt_fcf_pct} | {debt_total_pct} debt)"

        print(
            f"{r['year']:<6} {fcf_str:<15} {div_str:<30} {buy_str:<30} {debt_str:<30}"
        )

    # Additional info row with Capex and M&A
    print("\n" + "-" * 100)
    print(f"{'Year':<6} {'Capex':<25} {'M&A':<25} {'Cash Increase':<25}")
    print("-" * 100)

    for r in results:
        capex_abs = f"${r['capex'] / 1_000_000:,.0f}M"
        capex_pct = f"({r['capex_pct']:.1f}%)" if r["capex_pct"] else "(N/A)"
        capex_str = f"{capex_abs} {capex_pct}"

        ma_abs = f"${r['acquisitions'] / 1_000_000:,.0f}M"
        ma_pct = f"({r['acquisitions_pct']:.1f}%)" if r["acquisitions_pct"] else "(N/A)"
        ma_str = f"{ma_abs} {ma_pct}"

        cash_abs = f"${r['cash_increase'] / 1_000_000:,.0f}M"
        cash_pct = (
            f"({r['cash_increase_pct']:.1f}%)" if r["cash_increase_pct"] else "(N/A)"
        )
        cash_str = f"{cash_abs} {cash_pct}"

        print(f"{r['year']:<6} {capex_str:<25} {ma_str:<25} {cash_str:<25}")

    print("\n" + "=" * 80)
