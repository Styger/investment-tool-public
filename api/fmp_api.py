import requests
from datetime import datetime, timedelta
from typing import Optional, Tuple
import os
import sys
from utils.config_load import load_config


def resource_path(relative_path):
    """Pfad zur Datei – funktioniert in PyInstaller & VS Code"""
    try:
        # Wenn PyInstaller läuft
        base_path = sys._MEIPASS
    except AttributeError:
        # Wenn in VS Code ausgeführt
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


def get_api_key():
    config = load_config()
    return config.get("FMP_API_KEY", "")


def get_balance_sheet(ticker, limit=20):
    api_key = get_api_key()
    url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?limit={limit}&apikey={api_key}"
    response = requests.get(url)
    return response.json()


def get_income_statement(ticker, limit=20):
    api_key = get_api_key()
    url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?limit={limit}&apikey={api_key}"
    response = requests.get(url)
    return response.json()


def get_cashflow_statement(ticker, limit=20):
    api_key = get_api_key()
    url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?limit={limit}&apikey={api_key}"
    return requests.get(url).json()


def get_key_metrics(ticker, limit=20):
    api_key = get_api_key()
    url = f"https://financialmodelingprep.com/api/v3/key-metrics/{ticker}?limit={limit}&apikey={api_key}"
    return requests.get(url).json()


def get_dcf(ticker):
    api_key = get_api_key()
    url = f"https://financialmodelingprep.com/api/v3/discounted-cash-flow/{ticker}?apikey={api_key}"
    return requests.get(url).json()


def fetch_historical_price_json(ticker, date):
    """
    Low-level HTTP: fetch raw JSON for a specific date (from=to=date).
    Keep it simple so it's easy to mock in tests.
    """
    api = get_api_key()
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}"
    params = {"from": date, "to": date, "apikey": api}
    return requests.get(url, params=params).json()


def get_year_data_by_range(ticker, start_year, years=4):
    income = get_income_statement(ticker)
    cashflow = get_cashflow_statement(ticker)
    metrics = get_key_metrics(ticker)

    def get_by_year(data, year):
        for entry in data:
            if str(entry.get("calendarYear")) == str(year):
                return entry
        return {}

    results = []
    book_list, eps_list, revenue_list, cashflow_list = [], [], [], []

    for year in range(start_year, start_year + years + 1):
        i = get_by_year(income, year)
        c = get_by_year(cashflow, year)
        m = get_by_year(metrics, year)

        revenue = i.get("revenue", 0) / 1_000_000
        fcf = c.get("freeCashFlow", 0) / 1_000_000
        eps = i.get("eps", 0)
        roic = m.get("roic", None)

        results.append(
            {
                "Year": year,
                "Revenue (Mio)": round(revenue, 2),
                "Free Cash Flow (Mio)": round(fcf, 2),
                "EPS": round(eps, 2),
                "ROIC": f"{round(roic * 100, 2)} %" if roic is not None else "–",
            }
        )

        book_list.append(m.get("bookValuePerShare", 0))
        eps_list.append(i.get("eps", 0))
        revenue_list.append(m.get("revenuePerShare", 0))
        cashflow_list.append(m.get("operatingCashFlowPerShare", 0))

    mos_metrics = {
        "book": book_list,
        "eps": eps_list,
        "revenue": revenue_list,
        "cashflow": cashflow_list,
    }

    return results, mos_metrics


def get_price_on_date(ticker, date):
    """
    High-level parsing: extract the closing price from the fetched JSON.
    """
    print(f"Requesting stock price for {ticker} on {date}")
    data = fetch_historical_price_json(ticker, date)
    if not data:
        print(f"No data returned for {ticker} on {date}")
        return None

    historical = data.get("historical")
    if historical:
        price = historical[0].get("close")
        print(f"Price found: {price}")
        return price
    else:
        print(f"No price found for {ticker} on {date}")
        return None


def get_valid_price(
    ticker: str, base_date_str: str
) -> Tuple[Optional[float], Optional[str]]:
    base_date = datetime.strptime(base_date_str, "%Y-%m-%d")
    for i in range(14):
        current_date = base_date - timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        price = get_price_on_date(ticker, date_str)
        print(f"Trying {ticker} on {date_str}: {price}")
        if price:
            return price, date_str

    print(
        f"No valid stock price found for {ticker} from {base_date_str} within 14 days"
    )
    return None, None
