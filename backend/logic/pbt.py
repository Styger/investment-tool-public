from typing import List, Dict, Tuple, Optional
import sys
from pathlib import Path

# Stelle sicher, dass das Root-Verzeichnis im Python-Path ist
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.api import fmp_api


def _calculate_pbt_price(
    fcf: float, growth_rate: float, return_full_table: bool = False
) -> Tuple[float, float, Optional[List[Dict]]]:
    """
    Berechnet Kaufpreis (8-Jahres-Payback) und fairen Wert (Doppelt).
    """
    years = 8
    total = 0.0
    table = []

    for year in range(years + 1):
        if year == 0:
            income = fcf
        else:
            income = fcf * ((1 + growth_rate) ** year)

        if year > 0:
            total += income

        row = {
            "Jahr": year,
            "Einnahme": round(income, 2),
            "Summe_Cashflows": round(total, 2),
        }
        table.append(row)

    buy_price = round(table[8]["Summe_Cashflows"], 2)
    fair_value = round(buy_price * 2, 2)

    if return_full_table:
        return buy_price, fair_value, table
    return buy_price, fair_value, None


def _get_pbt_result(ticker: str, year: int, growth_rate: float) -> Optional[dict]:
    """
    Holt PBT-Daten für ein bestimmtes Jahr - ähnlich wie _get_ten_cap_result
    """
    try:
        # FCF pro Aktie holen
        key_metrics = fmp_api.get_key_metrics(ticker, limit=20)
        fcf = None

        for entry in key_metrics:
            if str(entry.get("calendarYear")) == str(year):
                fcf = entry.get("freeCashFlowPerShare")
                break

        if fcf is None:
            print(f"Kein FCF pro Aktie für Jahr {year} gefunden.")
            return None

        # Buy Price und Fair Value berechnen
        buy_price, fair_value, _ = _calculate_pbt_price(fcf, growth_rate, False)

        # Aktuellen Aktienkurs holen
        current_price = None
        price_comparison = "N/A"
        percentage_diff_fair = 0
        percentage_diff_buy = 0

        try:
            current_price = fmp_api.get_current_price(ticker)

            if current_price is not None and fair_value > 0:
                # Vergleich mit Fair Value
                percentage_diff_fair = ((current_price - fair_value) / fair_value) * 100

                # Vergleich mit Buy Price
                percentage_diff_buy = ((current_price - buy_price) / buy_price) * 100

                if current_price <= buy_price:
                    price_comparison = (
                        f"Below buy price by {abs(percentage_diff_buy):.1f}%"
                    )
                elif current_price <= fair_value:
                    price_comparison = (
                        f"Below fair value by {abs(percentage_diff_fair):.1f}%"
                    )
                else:
                    price_comparison = f"Overvalued by {abs(percentage_diff_fair):.1f}%"

        except Exception as e:
            print(f"Could not fetch current price for {ticker}: {e}")

        # Investment Recommendation
        investment_recommendation = _get_investment_recommendation(
            current_price, fair_value, buy_price
        )

        return {
            "ticker": ticker,
            "year": year,
            "fcf_per_share": fcf,
            "growth_rate": growth_rate,
            "buy_price": buy_price,
            "fair_value": fair_value,
            "current_stock_price": current_price,
            "price_comparison": price_comparison,
            "percentage_diff_fair": percentage_diff_fair,
            "percentage_diff_buy": percentage_diff_buy,
            "investment_recommendation": investment_recommendation,
        }

    except Exception as e:
        print(f"Error in _get_pbt_result: {e}")
        return None


def _get_investment_recommendation(
    current_price: float, fair_value: float, buy_price: float
) -> str:
    """
    Gibt eine Investitionsempfehlung basierend auf den Preisvergleichen.
    """
    if current_price is None or current_price <= 0:
        return "No price data available"

    if current_price <= buy_price:
        return "Strong Buy (At or below payback price)"
    elif current_price <= fair_value:
        return "Buy (Below fair value)"
    elif current_price <= fair_value * 1.1:
        return "Hold (Near fair value)"
    else:
        return "Avoid (Overvalued)"


def calculate_pbt_from_ticker(
    ticker: str,
    year: int,
    growth_estimate: float,
    return_full_table: bool = False,
) -> Tuple[float, float, Optional[List[Dict]], Dict]:
    """
    Legacy-Funktion für Kompatibilität - verwendet _get_pbt_result
    """
    result = _get_pbt_result(ticker, year, growth_estimate)

    if not result:
        raise ValueError(f"Could not calculate PBT for {ticker} in {year}")

    # Tabelle nur wenn explizit angefordert
    table = None
    if return_full_table:
        key_metrics = fmp_api.get_key_metrics(ticker, limit=20)
        fcf = None
        for entry in key_metrics:
            if str(entry.get("calendarYear")) == str(year):
                fcf = entry.get("freeCashFlowPerShare")
                break

        if fcf:
            _, _, table = _calculate_pbt_price(fcf, growth_estimate, True)

    # Legacy price_info Format
    price_info = {
        "Current Stock Price": result["current_stock_price"] or 0.0,
        "Buy Price (8Y Payback)": result["buy_price"],
        "Fair Value (2x Payback)": result["fair_value"],
        "Price Comparison": result["price_comparison"],
        "% vs Buy Price": result["percentage_diff_buy"],
        "% vs Fair Value": result["percentage_diff_fair"],
        "FCF per Share": result["fcf_per_share"],
        "Investment Recommendation": result["investment_recommendation"],
    }

    return result["buy_price"], result["fair_value"], table, price_info


def calculate_pbt_with_comparison(
    ticker: str, year: int, growth_rate: float
) -> Optional[dict]:
    """
    Neue Funktion analog zu calculate_ten_cap_with_comparison
    """
    return _get_pbt_result(ticker, year, growth_rate)


default_language = {
    "pbt_calc_title": "PBT Analyse für",
    "pbt_year": "Jahr",
    "pbt_income": "Einnahme",
    "pbt_cumulative": "Kumuliert",
    "pbt_fcf_per_share": "FCF pro Aktie:",
    "pbt_growth_rate": "Wachstumsrate:",
    "pbt_buy_price": "Buy Price (8Y Payback):",
    "pbt_fair_value": "Fair Value (2x):",
    "current_stock_price": "Current Stock Price:",
    "price_comparison": "Price vs. Fair Value:",
}


def _format_pbt_report(data: dict, table: List[Dict], language: dict) -> str:
    """
    Formatiert einen detaillierten PBT Report mit Cashflow-Tabelle
    """
    report = []
    report.append(
        f"\n{language['pbt_calc_title']} {data['ticker'].upper()} ({data['year']})"
    )
    report.append("=" * 60)
    report.append(
        f"{language['pbt_fcf_per_share']:25}  ${data['fcf_per_share']:>10,.2f}"
    )
    report.append(
        f"{language['pbt_growth_rate']:25}  {data['growth_rate'] * 100:>10.1f}%"
    )
    report.append("-" * 60)

    # Cashflow Tabelle
    report.append(f"\n{'Jahr':>6} | {'Einnahme':>15} | {'Kumuliert':>15}")
    report.append("-" * 60)

    for row in table:
        year = row["Jahr"]
        income = row["Einnahme"]
        cumulative = row["Summe_Cashflows"]

        marker = ""
        if year == 8:
            marker = " ← Buy Price"

        report.append(f"{year:>6} | ${income:>14,.2f} | ${cumulative:>14,.2f}{marker}")

    report.append("=" * 60)
    report.append(f"{language['pbt_buy_price']:25}  ${data['buy_price']:>10,.2f}")
    report.append(f"{language['pbt_fair_value']:25}  ${data['fair_value']:>10,.2f}")

    # Current Price und Vergleich hinzufügen
    if data.get("current_stock_price") is not None:
        report.append(
            f"{language['current_stock_price']:25}  ${data['current_stock_price']:>10,.2f}"
        )
        report.append(
            f"{language['price_comparison']:25} {data['price_comparison']:>15}"
        )

    return "\n".join(report)


def print_pbt_analysis(
    ticker: str, year: int, growth_rate: float, language: dict = None
):
    """
    Druckt eine detaillierte PBT Analyse mit Cashflow-Tabelle
    """
    if language is None:
        language = default_language

    # Hole die Basis-Daten
    result_data = _get_pbt_result(ticker, year, growth_rate)
    if not result_data:
        print(f"[ERROR] Could not find complete data for {ticker.upper()} in {year}")
        print(f"{year}: N/A")
        return

    # Generiere die detaillierte Tabelle
    key_metrics = fmp_api.get_key_metrics(ticker, limit=20)
    fcf = None
    for entry in key_metrics:
        if str(entry.get("calendarYear")) == str(year):
            fcf = entry.get("freeCashFlowPerShare")
            break

    if not fcf:
        print(f"[ERROR] Could not find FCF for {ticker.upper()} in {year}")
        return

    _, _, table = _calculate_pbt_price(fcf, growth_rate, return_full_table=True)

    # Drucke den formatierten Report
    print(_format_pbt_report(result_data, table, language))


if __name__ == "__main__":
    ticker = "aapl"
    year = 2024
    growth = 0.2

    result = _get_pbt_result(ticker, year, growth)

    if result:
        print(f"\n=== PBT Analysis for {ticker.upper()} ===")
        print(f"FCF per Share ({year}): ${result['fcf_per_share']:.2f}")
        print(f"Growth Rate: {growth * 100:.0f}%")
        print(f"\n--- Valuation ---")
        print(f"Buy Price (8Y Payback):  ${result['buy_price']:.2f}")
        print(f"Fair Value (2x):         ${result['fair_value']:.2f}")
        print(f"\n--- Current Market ---")
        print(f"Current Price:           ${result['current_stock_price']:.2f}")
        print(f"Price Comparison:        {result['price_comparison']}")
        print(f"Recommendation:          {result['investment_recommendation']}")
        print(f"\n--- Price Differences ---")
        print(f"vs Buy Price:            {result['percentage_diff_buy']:+.1f}%")
        print(f"vs Fair Value:           {result['percentage_diff_fair']:+.1f}%")
