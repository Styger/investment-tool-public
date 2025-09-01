import logging
from typing import Dict, List
import api.fmp_api

import pandas as pd


def _calculate_cagr(start, end, years):
    """
    Calculates the Compound Annual Growth Rate (CAGR) between two values over a specified time period.

    CAGR = (End Value / Start Value)^(1/years) - 1

    Args:
        start (float): Initial value
        end (float): Final value
        years (float): Number of years between start and end value

    Returns:
        float: CAGR as a decimal (e.g., 0.15 for 15% growth)
               Returns 0 if input values are invalid (negative, zero, or non-numeric)
    """
    logging.debug(f"calculate_cagr(start={start}, end={end}, years={years})")
    try:
        start = float(start)
        end = float(end)
        years = float(years)
    except Exception as e:
        logging.warning(f"Conversion failed: {e}")
        return 0

    if start <= 0 or end <= 0 or years <= 0:
        logging.warning("Invalid input for CAGR calculation. Returning 0.")
        return 0

    return (end / start) ** (1 / years) - 1


def _auto_detect_year_column(df: pd.DataFrame) -> str:
    """Findet die richtige Jahres-Spalte im DataFrame."""
    for col in df.columns:
        if col.strip().lower() == "year":
            return col
    raise ValueError("Keine gültige 'year'-Spalte gefunden.")


def _mos_growth_estimate_auto(
    data_dict: Dict[str, List[float]],
    start_year: int,
    end_year: int,
    period_years: int = 5,
    known_start_year: int = None,  # optional, falls bekannt
) -> Dict[str, float]:
    """
    Calculates CAGR metrics from start_year to end_year, inferring the base year from data or using known_start_year.
    """
    metrics = [v for v in data_dict.values() if isinstance(v, list)]
    if not metrics:
        raise ValueError("No valid metric data found.")

    num_years = len(metrics[0])

    # Entweder von außen bekannt, oder automatisch annehmen: letzte Zahl ist end_year
    if known_start_year:
        earliest_possible_year = known_start_year
    else:
        earliest_possible_year = end_year - (num_years - 1)

    start_index = start_year - earliest_possible_year
    end_index = end_year - earliest_possible_year

    if start_index < 0 or end_index >= num_years:
        raise ValueError(
            f"Insufficient data range to compute CAGR (need years {start_year}-{end_year}, but data only covers {earliest_possible_year}-{earliest_possible_year + num_years - 1})"
        )

    details = {}
    growths = []

    for key, values in data_dict.items():
        if len(values) <= end_index:
            details[key] = 0
            continue

        start = values[start_index]
        end = values[end_index]

        if start > 0 and end > 0:
            cagr = _calculate_cagr(start, end, period_years)
            growths.append(cagr)
            details[key] = round(cagr * 100, 2)
        else:
            details[key] = 0
            growths.append(0)

    avg_growth = sum(growths) / len(growths) if growths else 0
    details["avg"] = round(avg_growth * 100, 2)

    return details


def run_analysis(ticker: str, start_year: int, end_year: int, period_years: int = 10):
    """
    Führt die CAGR-Analyse für einen gegebenen Ticker durch.
    Gibt eine Tabelle mit jährlichen CAGR-Werten aus.
    """
    required_years = end_year - start_year
    data, mos_input = api.fmp_api.get_year_data_by_range(
        ticker, start_year, years=required_years
    )
    df = pd.DataFrame(data)

    year_col = _auto_detect_year_column(df)
    year_range = sorted(df[year_col].astype(int).tolist())
    earliest_year = min(year_range)
    latest_year = max(year_range)

    print(f"\n==== {ticker.upper()} Yearly CAGR ({period_years}y periods) ====\n")

    results_list = []

    for start in range(earliest_year, latest_year - period_years + 1):
        end = start + period_years
        try:
            result = _mos_growth_estimate_auto(
                data_dict=mos_input,
                start_year=start,
                end_year=end,
                period_years=period_years,
                known_start_year=earliest_year,
            )
            result["from"] = start
            result["to"] = end
            results_list.append(result)
        except ValueError as e:
            print(f"Skipping {start}-{end}: {e}")

    if results_list:
        result_df = pd.DataFrame(results_list)
        cols = ["from", "to", "book", "eps", "revenue", "cashflow", "avg"]
        result_df = result_df[cols]
        print(result_df.to_string(index=False))
    else:
        print("Keine gültigen CAGR-Zeiträume gefunden.")


def _main():
    #  Hier nur Parameter definieren
    ticker = "five"  # z. B. 2669.HK
    start_year = 2010
    end_year = 2025
    period_years = 5

    run_analysis(
        ticker=ticker,
        start_year=start_year,
        end_year=end_year,
        period_years=period_years,
    )
    # hier der AUfruf der Fuktion für die MOS-Berechnung
    # calculate_intrinsic_value(eps_now, growth_rate, target_year)


# in logic/cagr.py
def compute_cagr(start_value: float, end_value: float, years: int) -> float:
    if start_value <= 0 or end_value <= 0 or years <= 0:
        raise ValueError("All inputs must be positive.")
    return (end_value / start_value) ** (1 / years) - 1


if __name__ == "__main__":
    _main()
