from typing import Dict, List, Optional
import sys
from pathlib import Path

# Stelle sicher, dass das Root-Verzeichnis im Python-Path ist
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.api import fmp_api


def calculate_debt_metrics_from_ticker(
    ticker: str, year: int, use_total_debt: bool = False
) -> Dict:
    """
    Calculates debt metrics for a company for a single year.

    Args:
        ticker: Stock symbol
        year: Year for analysis
        use_total_debt: If True, use total debt; if False, use long-term debt only

    Returns:
        Dict with debt metrics (pure numbers, no text/ratings)
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

    # Extract values
    long_term_debt = bs_data.get("longTermDebt", 0)
    total_debt = bs_data.get("totalDebt", 0)
    net_income = is_data.get("netIncome", 0)

    # Choose which debt to use for ratio calculation
    debt_used = total_debt if use_total_debt else long_term_debt

    # Calculate ratio
    if net_income <= 0:
        debt_to_income_ratio = None  # Cannot calculate with negative/zero income
    else:
        debt_to_income_ratio = debt_used / net_income

    # Return pure data
    result = {
        "ticker": ticker.upper(),
        "year": year,
        "long_term_debt": long_term_debt,
        "total_debt": total_debt,
        "debt_used": debt_used,
        "use_total_debt": use_total_debt,
        "net_income": net_income,
        "debt_to_income_ratio": debt_to_income_ratio,
    }

    print("Debt Analysis Result: %s", result)
    return result


def calculate_debt_metrics_multi_year(
    ticker: str, start_year: int, end_year: int, use_total_debt: bool = False
) -> List[Dict]:
    """
    Calculates debt metrics for a company across multiple years.

    Args:
        ticker: Stock symbol
        start_year: Starting year
        end_year: Ending year
        use_total_debt: If True, use total debt; if False, use long-term debt only

    Returns:
        List of dicts with debt metrics for each year
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

        # Extract values
        long_term_debt = bs_data.get("longTermDebt", 0)
        total_debt = bs_data.get("totalDebt", 0)
        net_income = is_data.get("netIncome", 0)

        # Choose which debt to use for ratio calculation
        debt_used = total_debt if use_total_debt else long_term_debt

        # Calculate ratio
        if net_income <= 0:
            debt_to_income_ratio = None
        else:
            debt_to_income_ratio = debt_used / net_income

        results.append(
            {
                "ticker": ticker.upper(),
                "year": year,
                "long_term_debt": long_term_debt,
                "total_debt": total_debt,
                "debt_used": debt_used,
                "use_total_debt": use_total_debt,
                "net_income": net_income,
                "debt_to_income_ratio": debt_to_income_ratio,
            }
        )

    print(
        f"Debt Analysis for {ticker} from {start_year} to {end_year}: {len(results)} years"
    )
    return results


if __name__ == "__main__":
    # Example analysis - single year with long-term debt
    print("\n=== Single Year Analysis - Long-term Debt ===")
    result = calculate_debt_metrics_from_ticker(
        ticker="AAPL", year=2024, use_total_debt=False
    )
    print(result)

    # Example analysis - single year with total debt
    print("\n=== Single Year Analysis - Total Debt ===")
    result = calculate_debt_metrics_from_ticker(
        ticker="AAPL", year=2024, use_total_debt=True
    )
    print(result)

    # Example analysis - multiple years with long-term debt
    print("\n=== Multi Year Analysis - Long-term Debt ===")
    results = calculate_debt_metrics_multi_year(
        ticker="AAPL", start_year=2020, end_year=2024, use_total_debt=False
    )
    for r in results:
        print(r)

    # Example analysis - multiple years with total debt
    print("\n=== Multi Year Analysis - Total Debt ===")
    results = calculate_debt_metrics_multi_year(
        ticker="AAPL", start_year=2020, end_year=2024, use_total_debt=True
    )
    for r in results:
        print(r)
