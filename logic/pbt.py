from matplotlib import ticker
import api.fmp_api
from typing import List, Dict, Tuple, Optional


def _calculate_pbt_price(
    fcf: float, growth_rate: float, return_full_table: bool = False
) -> Tuple[float, Optional[List[Dict]]]:
    """
    Berechnet den maximalen Kaufpreis einer Aktie basierend auf der Payback Time Methode.
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
            "PBT_Preis": round(total, 2) if year == 8 else None,
        }
        table.append(row)

    if return_full_table:
        return round(table[8]["Summe_Cashflows"], 2), table
    return round(table[8]["Summe_Cashflows"], 2), None


def calculate_pbt_from_ticker(
    ticker: str,
    year: int,
    growth_estimate: float,
    return_full_table: bool = False,
) -> Tuple[float, Optional[List[Dict]], Dict]:
    """
    Holt den FCF pro Aktie für ein bestimmtes Jahr und berechnet die Payback Time.
    Zusätzlich wird der aktuelle Aktienkurs geholt für Vergleiche.

    :return: PBT-Preis, optional: Tabelle, Preisvergleich-Dict
    """
    try:
        # FCF pro Aktie holen
        key_metrics = api.fmp_api.get_key_metrics(ticker, limit=20)
        fcf = None

        for entry in key_metrics:
            if str(entry.get("calendarYear")) == str(year):
                fcf = entry.get("freeCashFlowPerShare")
                break

        if fcf is None:
            raise ValueError(f"Kein FCF pro Aktie für Jahr {year} gefunden.")

        # PBT-Preis berechnen
        pbt_price, table = _calculate_pbt_price(fcf, growth_estimate, return_full_table)

        # Aktuellen Aktienkurs holen
        current_price = 0
        price_comparison = "N/A"
        percentage_diff = 0

        try:
            current_price = api.fmp_api.get_current_price(ticker)
            # Vergleich mit PBT-Preis nur wenn beide Preise verfügbar sind
            if current_price is not None and pbt_price > 0:
                percentage_diff = ((current_price - pbt_price) / pbt_price) * 100
                if current_price > pbt_price:
                    price_comparison = f"Overvalued by {abs(percentage_diff):.1f}%"
                elif current_price < pbt_price:
                    price_comparison = f"Undervalued by {abs(percentage_diff):.1f}%"
                else:
                    price_comparison = "Fair valued"
            else:
                current_price = 0  # Fallback falls None

        except Exception as e:
            print(f"Could not fetch current price for {ticker}: {e}")
            current_price = 0

        # Preisvergleich-Daten
        price_info = {
            "Current Stock Price": round(current_price, 2) if current_price else 0.0,
            "PBT Price": round(pbt_price, 2),
            "Price vs PBT": price_comparison,
            "Percentage Difference": round(percentage_diff, 2),
            "FCF per Share": round(fcf, 2),
        }

        return pbt_price, table, price_info

    except Exception as e:
        print(f"PBT-Berechnung für {ticker.upper()} fehlgeschlagen: {e}")
        raise


if __name__ == "__main__":
    ticker = "aapl"
    year = 2024
    growth = 0.2

    price, table, price_info = calculate_pbt_from_ticker(
        ticker, year, growth, return_full_table=True
    )
    print(f"PBT-Kaufpreis: {price:.2f}")
    print(f"Aktueller Preis: {price_info['Current Stock Price']:.2f}")
    print(f"Bewertung: {price_info['Price vs PBT']}")
