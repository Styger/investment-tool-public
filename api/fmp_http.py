# api/fmp_http.py
import requests
from utils.config_load import load_config


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


def fetch_historical_price(ticker, date):
    """
    Fetches raw JSON data from the FMP API for a specific date.
    Returns None if the request fails.
    """
    api = get_api_key()
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}"
    params = {"from": date, "to": date, "apikey": api}
    return requests.get(url, params=params).json()
