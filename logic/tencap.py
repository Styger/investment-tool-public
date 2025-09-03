from api import fmp_api
from typing import Optional

language = {
    "ten_cap_calc_title": "TEN CAP Analyse für",
    "ten_cap_profit_before_tax": "Gewinn vor Steuern:",
    "ten_cap_depreciation": "+ Abschreibungen:",
    "ten_cap_working_capital": "Δ Working Capital:",
    "ten_cap_capex": "- 50% Maintenance CapEx:",
    "ten_cap_owner_earnings": "= Owner Earnings:",
    "ten_cap_shares": "Aktien (Mio):",
    "ten_cap_eps": "Earnings per Share:",
    "ten_cap_price": "TEN CAP Buy Price:",
    "current_stock_price": "Current Stock Price:",
    "price_comparison": "Price vs TEN CAP:",
}


def _calculate_owner_earnings(
    profit_before_tax: float,
    depreciation: float,
    working_capital_change: float,
    maintenance_capex: float,
) -> float:
    """
    Calculates Owner Earnings based on input values.
    All values should be in the same unit (millions).
    Working Capital Changes from Cash Flow Statement already have correct signs:
    - Increase in Receivables: negative (cash tied up)
    - Increase in Payables: positive (more financing)
    """
    # Check for zero values and log warnings
    if depreciation == 0:
        print("Depreciation is 0 - this is unusual and might indicate missing data")

    if working_capital_change == 0:
        print(
            "Working Capital change is 0 - this is unusual and might indicate missing data"
        )

    # Only 50% of Maintenance/CapEx is considered
    adjusted_maintenance = maintenance_capex * 0.5
    if adjusted_maintenance == 0:
        print(
            "Maintenance CapEx is 0 - this is unusual and might indicate missing data"
        )

    owner_earnings = (
        profit_before_tax
        + depreciation
        + working_capital_change  # Already contains all Working Capital changes with correct signs
        - adjusted_maintenance
    )

    return owner_earnings


def _calculate_working_capital_change(cashflow_data: dict) -> tuple:
    """
    Calculates the change in working capital from its components.
    All values from Cash Flow Statement already have correct signs:
    - Increase in Assets (Receivables): negative (cash tied up)
    - Increase in Liabilities (Payables): positive (more financing)

    Returns:
        tuple: (working_capital_change, components_dict)
    """
    MILLION = 1_000_000

    # Assets (negative when increasing)
    accounts_receivable_change = cashflow_data.get("accountsReceivables", 0) / MILLION

    # Liabilities (positive when increasing)
    accounts_payable_change = cashflow_data.get("accountsPayables", 0) / MILLION

    # Total Working Capital Change
    working_capital_change = (
        accounts_receivable_change  # Accounts Receivable
        + accounts_payable_change  # Accounts Payable
    )

    components = {
        "accounts_receivable": accounts_receivable_change,
        "accounts_payable": accounts_payable_change,
    }

    return working_capital_change, components


def _format_ten_cap_report(data: dict, language: dict) -> str:
    report = []
    report.append(
        f"\n{language['ten_cap_calc_title']} {data['ticker'].upper()} ({data['year']})"
    )
    report.append("-" * 50)
    report.append(
        f"{language['ten_cap_profit_before_tax']:25} ${data['profit_before_tax']:>10,.2f}M"
    )
    report.append(
        f"{language['ten_cap_depreciation']:25} ${data['depreciation']:>10,.2f}M"
    )
    wc = data["working_capital_change"]
    report.append(f"{language['ten_cap_working_capital']:25} ${wc:>10,.2f}M")
    report.append(
        f"{language['ten_cap_capex']:25} ${data['maintenance_capex'] * 0.5:>10,.2f}M"
    )
    report.append("-" * 50)
    report.append(
        f"{language['ten_cap_owner_earnings']:25} ${data['owner_earnings']:>10,.2f}M"
    )
    report.append(
        f"{language['ten_cap_shares']:25} {data['shares_outstanding']:>10,.2f}"
    )
    report.append(f"{language['ten_cap_eps']:25} ${data['earnings_per_share']:>10,.2f}")
    report.append("=" * 50)
    report.append(
        f"{language['ten_cap_price']:25} ${data['ten_cap_buy_price']:>10,.2f}"
    )

    # Current Price und Vergleich hinzufügen
    if data.get("current_stock_price") is not None:
        report.append(
            f"{language['current_stock_price']:25} ${data['current_stock_price']:>10,.2f}"
        )
        report.append(
            f"{language['price_comparison']:25} {data['price_vs_ten_cap']:>15}"
        )

    return "\n".join(report)


def _get_ten_cap_result(ticker: str, year: int) -> Optional[dict]:
    try:
        income_data = fmp_api.get_income_statement(ticker, limit=10)
        cashflow_data = fmp_api.get_cashflow_statement(ticker, limit=10)
        metrics = fmp_api.get_key_metrics(ticker, limit=10)

        if not income_data or not cashflow_data or not metrics:
            print(f"Could not get financial data for {ticker}")
            return None

        year_str = str(year)

        current_year_data = next(
            (d for d in income_data if str(d.get("calendarYear")) == year_str), None
        )
        current_cashflow = next(
            (d for d in cashflow_data if str(d.get("calendarYear")) == year_str), None
        )
        current_metrics = next(
            (d for d in metrics if str(d.get("calendarYear")) == year_str), None
        )

        if not current_year_data or not current_cashflow or not current_metrics:
            print(f"Could not find complete data for {year}")
            return None

        MILLION = 1_000_000
        profit_before_tax = current_year_data.get("incomeBeforeTax", 0) / MILLION
        depreciation = (
            current_cashflow.get("depreciationAndAmortization", 0)
            or current_cashflow.get("depreciation", 0)
            or current_cashflow.get("depreciationAmortizationDepletion", 0)
            or current_cashflow.get("depreciationDepletionAndAmortization", 0)
        ) / MILLION

        working_capital_change, wc_components = _calculate_working_capital_change(
            current_cashflow
        )
        maintenance_capex = abs(current_cashflow.get("capitalExpenditure", 0)) / MILLION

        shares_outstanding = (
            current_metrics.get("weightedAverageShsOut", 0)
            or current_metrics.get("weightedAverageShsOutDil", 0)
            or current_year_data.get("weightedAverageShsOut", 0)
            or current_year_data.get("weightedAverageShsOutDil", 0)
        ) / MILLION

        if shares_outstanding <= 0:
            print(f"No valid shares outstanding found for {ticker}")
            return None

        owner_earnings = _calculate_owner_earnings(
            profit_before_tax, depreciation, working_capital_change, maintenance_capex
        )

        eps = owner_earnings / shares_outstanding if shares_outstanding > 0 else 0
        ten_cap_price = eps / 0.10

        # Current Stock Price holen
        current_price = None
        price_comparison = "N/A"

        try:
            current_price = fmp_api.get_current_price(ticker)

            if current_price is not None and ten_cap_price > 0:
                percentage_diff = (
                    (current_price - ten_cap_price) / ten_cap_price
                ) * 100
                if current_price > ten_cap_price:
                    price_comparison = f"Overvalued by {abs(percentage_diff):.1f}%"
                elif current_price < ten_cap_price:
                    price_comparison = f"Undervalued by {abs(percentage_diff):.1f}%"
                else:
                    price_comparison = "Fair valued"

        except Exception as e:
            print(f"Could not fetch current price for {ticker}: {e}")

        return {
            "ticker": ticker,
            "year": year,
            "profit_before_tax": profit_before_tax,
            "depreciation": depreciation,
            "working_capital_change": working_capital_change,
            "maintenance_capex": maintenance_capex,
            "owner_earnings": owner_earnings,
            "shares_outstanding": shares_outstanding,
            "earnings_per_share": eps,
            "ten_cap_buy_price": ten_cap_price,
            "current_stock_price": current_price,
            "price_vs_ten_cap": price_comparison,
            "wc_components": wc_components,
        }

    except Exception as e:
        print(f"Error in get_ten_cap_result: {e}")
        return None


def print_ten_cap_analysis(ticker: str, year: int, language: dict):
    data = _get_ten_cap_result(ticker, year)
    if not data:
        print(f"[ERROR] Could not find complete data for {ticker.upper()} in {year}")
        print(f"{year}: N/A")
        return
    print(_format_ten_cap_report(data, language))


def calculate_ten_cap_price(ticker: str, year: int = None) -> Optional[float]:
    result = _get_ten_cap_result(ticker, year)
    return result["ten_cap_buy_price"] if result else None


def calculate_ten_cap_with_comparison(ticker: str, year: int = None) -> Optional[dict]:
    """
    Neue Funktion die sowohl TEN CAP Preis als auch Current Price mit Vergleich zurückgibt
    """
    return _get_ten_cap_result(ticker, year)


def _run():
    ticker = "evvty"
    test_years = [2022, 2023, 2024, 2025]

    print("\nTEN CAP Analysis for Multiple Years:\n")

    for year in test_years:
        result = _get_ten_cap_result(ticker, year)
        if result:
            print(_format_ten_cap_report(result, language))  # Nur diese Ausgabe
        else:
            print(f"Could not find complete data for {year}")
            print(f"{year}: N/A")


if __name__ == "__main__":
    # Test mit mehreren Jahren
    _run()
