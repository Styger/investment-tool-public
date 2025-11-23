# import api.fmp_api
from typing import List, Dict, Tuple, Optional
import sys
from pathlib import Path

# Stelle sicher, dass das Root-Verzeichnis im Python-Path ist
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.api import fmp_api


def _calculate_pbt_price(
    fcf: float, growth_rate: float, return_full_table: bool = False
) -> Tuple[float, Optional[List[Dict]]]:
    """
    Berechnet den fairen Wert (8-Jahres-Payback) ohne MOS.
    """
    years = 16
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
            "Fair_Value": round(total, 2) if year == 8 else None,
        }
        table.append(row)

    fair_value = round(table[8]["Summe_Cashflows"], 2)

    if return_full_table:
        return fair_value, table
    return fair_value, None


def calculate_pbt_from_ticker(
    ticker: str,
    year: int,
    growth_estimate: float,
    margin_of_safety: float = 0.25,  # Standard 25% MOS
    return_full_table: bool = False,
) -> Tuple[float, float, Optional[List[Dict]], Dict]:
    """
    Holt den FCF pro Aktie für ein bestimmtes Jahr und berechnet die Payback Time.

    Args:
        ticker: Aktien-Symbol
        year: Bezugsjahr für FCF
        growth_estimate: Wachstumsrate (z.B. 0.2 für 20%)
        margin_of_safety: Sicherheitsmarge (z.B. 0.25 für 25%)
        return_full_table: Ob die vollständige Tabelle zurückgegeben werden soll

    Returns:
        fair_value, buy_price_with_mos, optional_table, price_comparison_dict
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
            raise ValueError(f"Kein FCF pro Aktie für Jahr {year} gefunden.")

        # Fairen Wert berechnen (ohne MOS)
        fair_value, table = _calculate_pbt_price(
            fcf, growth_estimate, return_full_table
        )

        # Kaufpreis mit MOS berechnen
        buy_price_with_mos = fair_value * (1 - margin_of_safety)

        # Aktuellen Aktienkurs holen
        current_price = 0
        price_comparison = "N/A"
        percentage_diff_fair = 0
        percentage_diff_buy = 0

        try:
            current_price = fmp_api.get_current_price(ticker)

            if current_price is not None and fair_value > 0:
                # Vergleich mit fairem Wert (ohne MOS)
                percentage_diff_fair = ((current_price - fair_value) / fair_value) * 100
                if current_price > fair_value:
                    price_comparison = f"Overvalued by {abs(percentage_diff_fair):.1f}%"
                elif current_price < fair_value:
                    price_comparison = (
                        f"Undervalued by {abs(percentage_diff_fair):.1f}%"
                    )
                else:
                    price_comparison = "Fair valued"

                # Zusätzlicher Vergleich mit Kaufpreis (mit MOS)
                percentage_diff_buy = (
                    (current_price - buy_price_with_mos) / buy_price_with_mos
                ) * 100

            else:
                current_price = 0

        except Exception as e:
            print(f"Could not fetch current price for {ticker}: {e}")
            current_price = 0

        # Erweiterte Preisvergleich-Daten
        price_info = {
            "Current Stock Price": round(current_price, 2) if current_price else 0.0,
            "Fair Value (8Y Payback)": round(fair_value, 2),
            "Buy Price (with MOS)": round(buy_price_with_mos, 2),
            "Margin of Safety": f"{margin_of_safety * 100:.1f}%",
            "Price vs Fair Value": price_comparison,
            "Percentage Diff (Fair)": round(percentage_diff_fair, 2),
            "Percentage Diff (Buy)": round(percentage_diff_buy, 2),
            "FCF per Share": round(fcf, 2),
            "Investment Recommendation": _get_investment_recommendation(
                current_price, fair_value, buy_price_with_mos
            ),
        }

        return fair_value, buy_price_with_mos, table, price_info

    except Exception as e:
        print(f"PBT-Berechnung für {ticker.upper()} fehlgeschlagen: {e}")
        raise


def _get_investment_recommendation(
    current_price: float, fair_value: float, buy_price: float
) -> str:
    """
    Gibt eine Investitionsempfehlung basierend auf den Preisvergleichen.
    """
    if current_price <= 0:
        return "No price data available"

    if current_price <= buy_price:
        return "Strong Buy (Below MOS price)"
    elif current_price <= fair_value:
        return "Buy (Below fair value)"
    elif current_price <= fair_value * 1.1:
        return "Hold (Near fair value)"
    else:
        return "Avoid (Overvalued)"


if __name__ == "__main__":
    ticker = "aapl"
    year = 2024
    growth = 0.2
    mos = 0.5  # 25% Sicherheitsmarge

    fair_value, buy_price, table, price_info = calculate_pbt_from_ticker(
        ticker, year, growth, mos, return_full_table=True
    )

    print(f"=== PBT Analysis for {ticker.upper()} ===")
    print(f"Fair Value (8Y Payback): ${fair_value:.2f}")
    print(f"Buy Price (with {mos * 100:.0f}% MOS): ${buy_price:.2f}")
    print(f"Current Price: ${price_info['Current Stock Price']:.2f}")
    print(f"Bewertung: {price_info['Price vs Fair Value']}")
    print(f"Empfehlung: {price_info['Investment Recommendation']}")
