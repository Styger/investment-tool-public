from typing import Dict
import api.fmp_api


def calculate_mos_value_from_ticker(
    ticker: str, year: int, growth_rate: float, discount_rate=0.15, mos=0.50
) -> Dict:
    """
    Calculates the intrinsic value and MOS price based on EPS fetched from FMP and user-defined growth.
    Also fetches current stock price for comparison.
    """
    # Fetch EPS from financial data
    data, _ = api.fmp_api.get_year_data_by_range(ticker, start_year=year, years=0)
    if not data or "EPS" not in data[0] or data[0]["EPS"] <= 0:
        print(f"No valid EPS data found for {ticker} in year {year}")
        return {
            "EPS_10y": 0,
            "Future Value": 0,
            "Fair Value Today": 0,
            "MOS Price (50%)": 0,
            "Current Stock Price": 0,
            "Price vs Fair Value": "N/A",
            "Percentage Difference": 0,
        }

    eps_now = data[0]["EPS"]

    # Calculate intrinsic values
    eps_10y = eps_now * ((1 + growth_rate) ** 10)
    future_pe = growth_rate * 200
    future_value = eps_10y * future_pe
    fair_value_today = future_value / ((1 + discount_rate) ** 10)
    mos_price = fair_value_today * (1 - mos)

    # Get current stock price - KORRIGIERT für neue Funktion
    current_price = 0
    price_comparison = "N/A"
    percentage_diff = 0

    try:
        # Neue Signatur: get_current_price gibt direkt float oder None zurück
        current_price = api.fmp_api.get_current_price(ticker)

        # Prüfe ob ein gültiger Preis zurückgegeben wurde
        if current_price is not None:
            # Calculate comparison with fair value
            if fair_value_today > 0:
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
            current_price = 0  # Fallback falls None

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
        "MOS Price (50%)": round(mos_price, 2),
        "Current Stock Price": round(current_price, 2) if current_price else 0.0,
        "Price vs Fair Value": price_comparison,
        "Percentage Difference": round(percentage_diff, 2),
    }

    print("Intrinsic Value Result: %s", result)
    return result


if __name__ == "__main__":
    result = calculate_mos_value_from_ticker(ticker="AAPL", year=2024, growth_rate=0.2)
    print(result)
