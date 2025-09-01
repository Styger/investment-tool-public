from typing import Dict
from api import fmp_api

# from ten_cap import calculate_ten_cap_price  # optional
# from mos import mos_growth_estimate  # optional


def calculate_mos_value_from_ticker(
    ticker: str, year: int, growth_rate: float, discount_rate=0.15, mos=0.50
) -> Dict:
    """
    Calculates the intrinsic value and MOS price based on EPS fetched from FMP and user-defined growth.

    Args:
        ticker: Stock ticker symbol
        year: Starting year to fetch EPS
        growth_rate: Expected growth rate (decimal)
        discount_rate: Discount rate for present value (default: 15%)
        mos: Margin of Safety (default: 50%)

    Returns:
        Dictionary with intrinsic value calculation
    """
    # Fetch EPS from financial data
    data, _ = fmp_api.get_year_data_by_range(ticker, start_year=year, years=0)
    if not data or "EPS" not in data[0] or data[0]["EPS"] <= 0:
        print(f"No valid EPS data found for {ticker} in year {year}")
        return {
            "EPS_10y": 0,
            "Future Value": 0,
            "Fair Value Today": 0,
            "MOS Price (50%)": 0,
        }

    eps_now = data[0]["EPS"]

    eps_10y = eps_now * ((1 + growth_rate) ** 10)
    future_pe = growth_rate * 200
    future_value = eps_10y * future_pe
    fair_value_today = future_value / ((1 + discount_rate) ** 10)
    mos_price = fair_value_today * (1 - mos)

    result = {
        "Ticker": ticker.upper(),
        "Year": year,
        "Growth Rate": round(growth_rate * 100, 2),
        "EPS_now": round(eps_now, 2),
        "EPS_10y": round(eps_10y, 2),
        "Future Value": round(future_value, 2),
        "Fair Value Today": round(fair_value_today, 2),
        "MOS Price (50%)": round(mos_price, 2),
    }

    print("Intrinsic Value Result: %s", result)
    return result


if __name__ == "__main__":
    result = calculate_mos_value_from_ticker(ticker="AAPL", year=2024, growth_rate=0.2)
    print(result)
