from typing import Dict, List, Optional
import sys
from pathlib import Path

# Stelle sicher, dass das Root-Verzeichnis im Python-Path ist
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.api import fmp_api


def calculate_profitability_metrics_from_ticker(ticker: str, year: int) -> Dict:
    """
    Calculates profitability metrics for a company for a single year.
    Works for all stocks worldwide (not limited to US stocks).

    Args:
        ticker: Stock symbol
        year: Year for analysis

    Returns:
        Dict with profitability metrics (pure numbers, no text/ratings)
    """
    # Fetch Balance Sheet and Income Statement
    balance_sheet = fmp_api.get_balance_sheet(ticker, limit=20)
    income_statement = fmp_api.get_income_statement(ticker, limit=20)

    # Find data for the specified year
    def get_by_year(data, target_year):
        for entry in data:
            if str(entry.get("calendarYear")) == str(target_year):
                return entry
        return {}

    bs_data = get_by_year(balance_sheet, year)
    is_data = get_by_year(income_statement, year)

    # Extract Balance Sheet values
    total_assets = bs_data.get("totalAssets", 0)
    shareholders_equity = bs_data.get("totalStockholdersEquity", 0) or bs_data.get(
        "totalEquity", 0
    )

    # Extract Income Statement values
    revenue = is_data.get("revenue", 0)
    gross_profit = is_data.get("grossProfit", 0)
    operating_income = is_data.get("operatingIncome", 0)
    net_income = is_data.get("netIncome", 0)

    # Calculate Return Ratios
    roe = net_income / shareholders_equity if shareholders_equity > 0 else None
    roa = net_income / total_assets if total_assets > 0 else None

    # Calculate Margins (as decimals, will be converted to % in GUI)
    gross_margin = gross_profit / revenue if revenue > 0 else None
    operating_margin = operating_income / revenue if revenue > 0 else None
    net_margin = net_income / revenue if revenue > 0 else None

    # Calculate Efficiency
    asset_turnover = revenue / total_assets if total_assets > 0 else None

    # Return pure data
    result = {
        "ticker": ticker.upper(),
        "year": year,
        "revenue": revenue,
        "gross_profit": gross_profit,
        "operating_income": operating_income,
        "net_income": net_income,
        "total_assets": total_assets,
        "shareholders_equity": shareholders_equity,
        "roe": roe,
        "roa": roa,
        "gross_margin": gross_margin,
        "operating_margin": operating_margin,
        "net_margin": net_margin,
        "asset_turnover": asset_turnover,
    }

    print(f"Profitability Analysis Result: {result}")
    return result


def calculate_profitability_metrics_multi_year(
    ticker: str, start_year: int, end_year: int
) -> List[Dict]:
    """
    Calculates profitability metrics for a company across multiple years.

    Args:
        ticker: Stock symbol
        start_year: Starting year
        end_year: Ending year

    Returns:
        List of dicts with profitability metrics for each year
    """
    # Fetch all data once
    balance_sheet = fmp_api.get_balance_sheet(ticker, limit=20)
    income_statement = fmp_api.get_income_statement(ticker, limit=20)

    def get_by_year(data, target_year):
        for entry in data:
            if str(entry.get("calendarYear")) == str(target_year):
                return entry
        return {}

    results = []

    for year in range(start_year, end_year + 1):
        bs_data = get_by_year(balance_sheet, year)
        is_data = get_by_year(income_statement, year)

        # Extract Balance Sheet values
        total_assets = bs_data.get("totalAssets", 0)
        shareholders_equity = bs_data.get("totalStockholdersEquity", 0) or bs_data.get(
            "totalEquity", 0
        )

        # Extract Income Statement values
        revenue = is_data.get("revenue", 0)
        gross_profit = is_data.get("grossProfit", 0)
        operating_income = is_data.get("operatingIncome", 0)
        net_income = is_data.get("netIncome", 0)

        # Calculate Return Ratios
        roe = net_income / shareholders_equity if shareholders_equity > 0 else None
        roa = net_income / total_assets if total_assets > 0 else None

        # Calculate Margins
        gross_margin = gross_profit / revenue if revenue > 0 else None
        operating_margin = operating_income / revenue if revenue > 0 else None
        net_margin = net_income / revenue if revenue > 0 else None

        # Calculate Efficiency
        asset_turnover = revenue / total_assets if total_assets > 0 else None

        results.append(
            {
                "ticker": ticker.upper(),
                "year": year,
                "revenue": revenue,
                "gross_profit": gross_profit,
                "operating_income": operating_income,
                "net_income": net_income,
                "total_assets": total_assets,
                "shareholders_equity": shareholders_equity,
                "roe": roe,
                "roa": roa,
                "gross_margin": gross_margin,
                "operating_margin": operating_margin,
                "net_margin": net_margin,
                "asset_turnover": asset_turnover,
            }
        )

    print(
        f"Profitability Analysis for {ticker} from {start_year} to {end_year}: {len(results)} years"
    )
    return results


if __name__ == "__main__":
    ticker = "AAPL"
    year = 2024

    print("\n=== Single Year Profitability Analysis ===")
    result = calculate_profitability_metrics_from_ticker(ticker, year)

    print(f"\nProfitability Metrics for {ticker} ({year}):")
    print(f"ROE: {result['roe'] * 100:.2f}%" if result["roe"] else "ROE: N/A")
    print(f"ROA: {result['roa'] * 100:.2f}%" if result["roa"] else "ROA: N/A")
    print(
        f"Gross Margin: {result['gross_margin'] * 100:.2f}%"
        if result["gross_margin"]
        else "Gross Margin: N/A"
    )
    print(
        f"Operating Margin: {result['operating_margin'] * 100:.2f}%"
        if result["operating_margin"]
        else "Operating Margin: N/A"
    )
    print(
        f"Net Margin: {result['net_margin'] * 100:.2f}%"
        if result["net_margin"]
        else "Net Margin: N/A"
    )
    print(
        f"Asset Turnover: {result['asset_turnover']:.2f}x"
        if result["asset_turnover"]
        else "Asset Turnover: N/A"
    )

    print("\n=== Multi-Year Profitability Analysis ===")
    results = calculate_profitability_metrics_multi_year(ticker, 2022, 2024)

    print(
        f"\n{'Year':<6} {'ROE':<8} {'ROA':<8} {'Gross M.':<10} {'Op. M.':<10} {'Net M.':<8}"
    )
    print("-" * 60)
    for r in results:
        roe_str = f"{r['roe'] * 100:.1f}%" if r["roe"] else "N/A"
        roa_str = f"{r['roa'] * 100:.1f}%" if r["roa"] else "N/A"
        gm_str = f"{r['gross_margin'] * 100:.1f}%" if r["gross_margin"] else "N/A"
        om_str = (
            f"{r['operating_margin'] * 100:.1f}%" if r["operating_margin"] else "N/A"
        )
        nm_str = f"{r['net_margin'] * 100:.1f}%" if r["net_margin"] else "N/A"
        print(
            f"{r['year']:<6} {roe_str:<8} {roa_str:<8} {gm_str:<10} {om_str:<10} {nm_str:<8}"
        )
