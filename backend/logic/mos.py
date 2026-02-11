from typing import Dict
import sys
from pathlib import Path

# Stelle sicher, dass das Root-Verzeichnis im Python-Path ist
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.api import fmp_api


def calculate_mos_value_from_ticker(
    ticker: str,
    year: int,
    growth_rate: float,
    discount_rate: float = 0.15,
    margin_of_safety: float = 0.50,
) -> Dict:
    """
    Calculates the intrinsic value and MOS price based on EPS fetched from FMP and user-defined growth.
    Also fetches current stock price for comparison.

    Args:
        ticker: Stock symbol
        year: Base year for EPS
        growth_rate: Annual growth rate (e.g. 0.15 for 15%)
        discount_rate: Discount rate for present value calculation
        margin_of_safety: Safety margin (e.g. 0.25 for 25%)
    """
    # Fetch EPS from financial data
    data, _ = fmp_api.get_year_data_by_range(ticker, start_year=year, years=0)
    if not data or "EPS" not in data[0] or data[0]["EPS"] <= 0:
        print(f"No valid EPS data found for {ticker} in year {year}")
        return {
            "EPS_10y": 0,
            "Future Value": 0,
            "Fair Value Today": 0,
            "MOS Price": 0,
            "Current Stock Price": 0,
            "Price vs Fair Value": "N/A",
            "Percentage Difference": 0,
            "Margin of Safety": f"{margin_of_safety * 100:.1f}%",
        }

    eps_now = data[0]["EPS"]

    # Calculate intrinsic values
    eps_10y = eps_now * ((1 + growth_rate) ** 10)
    future_pe = growth_rate * 200
    future_value = eps_10y * future_pe
    fair_value_today = future_value / ((1 + discount_rate) ** 10)
    mos_price = fair_value_today * (1 - margin_of_safety)

    # Get current stock price
    current_price = 0
    price_comparison = "N/A"
    percentage_diff = 0

    try:
        current_price = fmp_api.get_current_price(ticker)

        if current_price is not None and fair_value_today > 0:
            # Calculate comparison with fair value (not MOS price)
            percentage_diff = (
                (current_price - fair_value_today) / fair_value_today
            ) * 100
            if current_price > fair_value_today:
                price_comparison = f"Overvalued by {abs(percentage_diff):.1f}%"
            elif current_price < fair_value_today:
                price_comparison = f"Undervalued by {abs(percentage_diff):.1f}%"
            else:
                price_comparison = "Fair valued"
        else:
            current_price = 0

    except Exception as e:
        print(f"Could not fetch current price for {ticker}: {e}")
        current_price = 0

    result = {
        "Ticker": ticker.upper(),
        "Year": year,
        "Growth Rate": round(growth_rate * 100, 2),
        "EPS_now": round(eps_now, 2),
        "EPS_10y": round(eps_10y, 2),
        "Future Value": round(future_value, 2),
        "Fair Value Today": round(fair_value_today, 2),
        "MOS Price": round(mos_price, 2),
        "Current Stock Price": round(current_price, 2) if current_price else 0.0,
        "Price vs Fair Value": price_comparison,
        "Percentage Difference": round(percentage_diff, 2),
        "Margin of Safety": f"{margin_of_safety * 100:.1f}%",
        "Investment Recommendation": _get_investment_recommendation(
            current_price, fair_value_today, mos_price
        ),
    }

    print("Intrinsic Value Result: %s", result)
    return result


def _get_investment_recommendation(
    current_price: float, fair_value: float, mos_price: float
) -> str:
    """
    Gibt eine Investitionsempfehlung basierend auf den Preisvergleichen.
    """
    if current_price <= 0:
        return "No price data available"

    if current_price <= mos_price:
        return "Strong Buy (Below MOS price)"
    elif current_price <= fair_value:
        return "Buy (Below fair value)"
    elif current_price <= fair_value * 1.1:
        return "Hold (Near fair value)"
    else:
        return "Avoid (Overvalued)"


def calculate_mos_from_data(
    ticker: str,
    current_price: float,
    income_statement: list,
    balance_sheet: list = None,
    cashflow: list = None,
    growth_rate: float = 0.10,
    discount_rate: float = 0.15,
    margin_of_safety: float = 0.50,
) -> Dict:
    """
    Calculate MOS using pre-fetched fundamentals and explicit price
    (For backtesting with historical data)

    Args:
        ticker: Stock symbol
        current_price: Price to use (historical or current)
        income_statement: Income statement data (FMP format)
        balance_sheet: Balance sheet data (optional)
        cashflow: Cashflow data (optional)
        growth_rate: Annual growth rate (e.g. 0.10 for 10%)
        discount_rate: Discount rate for present value
        margin_of_safety: Safety margin (e.g. 0.50 for 50%)

    Returns:
        Dict with MOS calculation results
    """
    # Get EPS from income statement
    if not income_statement or len(income_statement) == 0:
        return {
            "Ticker": ticker.upper(),
            "EPS_now": 0,
            "EPS_10y": 0,
            "Future Value": 0,
            "Fair Value Today": 0,
            "MOS Price": 0,
            "Current Stock Price": current_price,
            "Price vs Fair Value": "N/A",
            "Percentage Difference": 0,
            "Margin of Safety": f"{margin_of_safety * 100:.1f}%",
            "Investment Recommendation": "No data available",
        }

    # Get EPS (try both fields)
    eps_now = income_statement[0].get("eps") or income_statement[0].get("epsdiluted")

    if not eps_now or eps_now <= 0:
        return {
            "Ticker": ticker.upper(),
            "EPS_now": 0,
            "EPS_10y": 0,
            "Future Value": 0,
            "Fair Value Today": 0,
            "MOS Price": 0,
            "Current Stock Price": current_price,
            "Price vs Fair Value": "N/A",
            "Percentage Difference": 0,
            "Margin of Safety": f"{margin_of_safety * 100:.1f}%",
            "Investment Recommendation": "No valid EPS data",
        }

    # Calculate intrinsic values (SAME LOGIC AS ORIGINAL!)
    eps_10y = eps_now * ((1 + growth_rate) ** 10)
    future_pe = growth_rate * 200
    future_value = eps_10y * future_pe
    fair_value_today = future_value / ((1 + discount_rate) ** 10)
    mos_price = fair_value_today * (1 - margin_of_safety)

    # Calculate comparison with fair value
    price_comparison = "N/A"
    percentage_diff = 0

    if current_price > 0 and fair_value_today > 0:
        percentage_diff = ((current_price - fair_value_today) / fair_value_today) * 100
        if current_price > fair_value_today:
            price_comparison = f"Overvalued by {abs(percentage_diff):.1f}%"
        elif current_price < fair_value_today:
            price_comparison = f"Undervalued by {abs(percentage_diff):.1f}%"
        else:
            price_comparison = "Fair valued"

    result = {
        "Ticker": ticker.upper(),
        "Growth Rate": round(growth_rate * 100, 2),
        "EPS_now": round(eps_now, 2),
        "EPS_10y": round(eps_10y, 2),
        "Future Value": round(future_value, 2),
        "Fair Value Today": round(fair_value_today, 2),
        "MOS Price": round(mos_price, 2),
        "Current Stock Price": round(current_price, 2),
        "Price vs Fair Value": price_comparison,
        "Percentage Difference": round(percentage_diff, 2),
        "Margin of Safety": f"{margin_of_safety * 100:.1f}%",
        "Investment Recommendation": _get_investment_recommendation(
            current_price, fair_value_today, mos_price
        ),
        # Add these for easier access in backtesting
        "mos_percentage": percentage_diff,  # Negative = undervalued
        "fair_value": fair_value_today,
        "recommendation": _get_investment_recommendation(
            current_price, fair_value_today, mos_price
        ),
    }

    return result


if __name__ == "__main__":
    result = calculate_mos_value_from_ticker(
        ticker="AAPL",
        year=2024,
        growth_rate=0.10,
        margin_of_safety=0.50,  # 30% MOS
    )
    print(result)
