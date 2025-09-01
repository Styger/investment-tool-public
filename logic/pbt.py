from api import fmp_api

from typing import List, Dict, Tuple, Optional


def _calculate_pbt_price(
    fcf: float, growth_rate: float, return_full_table: bool = False
) -> Tuple[float, Optional[List[Dict]]]:
    """
    Berechnet den maximalen Kaufpreis einer Aktie basierend auf der Payback Time Methode.

    :param fcf: Free Cashflow pro Aktie (float)
    :param growth_rate: Wachstum pro Jahr als Dezimalzahl (z. B. 0.13 für 13 %)
    :param return_full_table: Wenn True, gibt zusätzlich Tabelle mit Jahr, Einnahme, kumuliertem CF zurück
    :return: float (PBT-Kaufpreis), optional: list of dicts
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
) -> Tuple[float, Optional[List[Dict]]]:
    """
    Holt den FCF pro Aktie für ein bestimmtes Jahr und berechnet die Payback Time.

    :param ticker: Aktienkürzel
    :param year: Basisjahr für den FCF
    :param growth_estimate: erwartetes Wachstum pro Jahr (z. B. 0.13 für 13 %)
    :param return_full_table: gibt vollständige Tabelle zurück
    :return: PBT-Preis, optional: Tabelle
    """
    try:
        key_metrics = fmp_api.get_key_metrics(ticker, limit=20)
        fcf = None

        for entry in key_metrics:
            if str(entry.get("calendarYear")) == str(year):
                fcf = entry.get("freeCashFlowPerShare")
                break

        if fcf is None:
            raise ValueError(f"Kein FCF pro Aktie für Jahr {year} gefunden.")

        return _calculate_pbt_price(fcf, growth_estimate, return_full_table)

    except Exception as e:
        print(f"PBT-Berechnung für {ticker.upper()} fehlgeschlagen: {e}")
        raise


if __name__ == "__main__":
    # Beispiel: Berechne PBT für evvty im Jahr 2024 mit 20 % Wachstum
    ticker = "evvty"
    year = 2024
    growth = 0.2

    price, table = calculate_pbt_from_ticker(
        ticker, year, growth, return_full_table=False
    )
    print(f"PBT-Kaufpreis: {price:.2f}")
    if table:
        for row in table:
            print(row)
