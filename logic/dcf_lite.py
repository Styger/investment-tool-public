# logic/dcf_lite.py
import api.fmp_api


def _extract_current_dcf(payload):
    """
    Normalize FMP DCF response to (dcf, stock_price, as_of_date).
    FMP v3 usually returns a list[dict] with keys: 'dcf', 'stockPrice', 'date'.
    We also guard against dict payloads or missing keys.
    """
    if not payload:
        return None, None, None

    item = None
    if isinstance(payload, list) and payload:
        item = payload[0]
    elif isinstance(payload, dict):
        item = payload
    else:
        return None, None, None

    dcf = item.get("dcf") or item.get("dcfValue") or item.get("value")
    price = item.get("stockPrice") or item.get("price")
    as_of = item.get("date") or item.get("asOfDate") or item.get("updatedAt")

    try:
        dcf = float(dcf) if dcf is not None else None
    except Exception:
        dcf = None
    try:
        price = float(price) if price is not None else None
    except Exception:
        price = None

    return dcf, price, as_of


def get_dcf_lite(ticker):
    """
    Fetches the current (unlevered) DCF for a ticker via FMP v3 and returns:
    {
      'ticker': 'AAPL',
      'dcf': 123.45 or None,
      'stock_price': 170.12 or None,
      'as_of': 'YYYY-MM-DD' or None
    }
    """
    res = {"ticker": ticker.upper(), "dcf": None, "stock_price": None, "as_of": None}

    # 1. Hole DCF-Daten
    try:
        payload = api.fmp_api.get_dcf(ticker)
    except Exception:
        payload = None

    # 2. Extrahiere DCF (so wie bisher)
    dcf, _, as_of = _extract_current_dcf(payload)
    if dcf is not None:
        res["dcf"] = dcf
    if as_of:
        res["as_of"] = as_of

    # 3. Hole Stock-Preis über unsere neue Funktion (nur Preis, kein Timestamp)
    try:
        price = api.fmp_api.get_current_price(ticker)
        if price is not None:
            res["stock_price"] = price
    except Exception as e:
        print(f"[get_dcf_lite] price fetch error: {e}")

    return res


def _print_dcf_lite(ticker):
    """
    Prints a compact DCF-Lite report to stdout for the given ticker.
    """
    data = get_dcf_lite(ticker)
    t = data["ticker"]

    print(f"\n==== {t} DCF (current) ====\n")
    if data["dcf"] is None:
        print("DCF: N/A")
    else:
        extra = f" (as of {data['as_of']})" if data.get("as_of") else ""
        print(f"DCF: ${data['dcf']:,.2f}{extra}")

    if data.get("stock_price") is not None:
        print(f"Stock Price: ${data['stock_price']:,.2f}")
    print()  # trailing newline


if __name__ == "__main__":
    # quick manual test
    _print_dcf_lite("AAPL")
