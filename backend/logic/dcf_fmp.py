# logic/dcf_fmp.py
import sys
from pathlib import Path

# Stelle sicher, dass das Root-Verzeichnis im Python-Path ist
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.api import fmp_api


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


def get_dcf_fmp(ticker, mos_percent=0.25):
    """
    Fetches the current (unlevered) DCF for a ticker via FMP v3 and returns:
    {
      'ticker': 'AAPL',
      'dcf': 123.45 or None,
      'buy_price': 92.59 or None,  # dcf * (1 - mos_percent)
      'stock_price': 170.12 or None,
      'as_of': 'YYYY-MM-DD' or None,
      'mos_percent': 0.25,
      'price_vs_fair': "Overvalued by 38.1%" or None,
      'price_vs_buy': "Above buy price by 84.0%" or None,
      'investment_recommendation': "Avoid (Overvalued)" or None
    }
    """
    res = {
        "ticker": ticker.upper(),
        "dcf": None,
        "buy_price": None,
        "stock_price": None,
        "as_of": None,
        "mos_percent": mos_percent,
        "price_vs_fair": None,
        "price_vs_buy": None,
        "investment_recommendation": None,
    }

    # 1. Hole DCF-Daten
    try:
        payload = fmp_api.get_dcf(ticker)
    except Exception:
        payload = None

    # 2. Extrahiere DCF (so wie bisher)
    dcf, _, as_of = _extract_current_dcf(payload)
    if dcf is not None:
        res["dcf"] = dcf
        res["buy_price"] = dcf * (1 - mos_percent)
    if as_of:
        res["as_of"] = as_of

    # 3. Hole Stock-Preis über unsere neue Funktion (nur Preis, kein Timestamp)
    try:
        price = fmp_api.get_current_price(ticker)
        if price is not None:
            res["stock_price"] = price
    except Exception as e:
        print(f"[get_dcf_fmp] price fetch error: {e}")

    # 4. Berechne Vergleiche und Empfehlung
    if res["dcf"] and res["stock_price"]:
        dcf_val = res["dcf"]
        buy_val = res["buy_price"]
        current = res["stock_price"]

        # Fair Value Vergleich
        fair_ratio = (current / dcf_val - 1) * 100
        if fair_ratio > 0:
            res["price_vs_fair"] = f"Overvalued by {fair_ratio:.1f}%"
        else:
            res["price_vs_fair"] = f"Undervalued by {abs(fair_ratio):.1f}%"

        # Buy Price Vergleich
        buy_ratio = (current / buy_val - 1) * 100
        if buy_ratio > 0:
            res["price_vs_buy"] = f"Above buy price by {buy_ratio:.1f}%"
        else:
            res["price_vs_buy"] = f"Below buy price by {abs(buy_ratio):.1f}%"

        # Investment Empfehlung
        res["investment_recommendation"] = _get_investment_recommendation(
            current, dcf_val, buy_val
        )

    return res


def _get_investment_recommendation(current_price, fair_value, buy_price):
    """Gibt eine Investitionsempfehlung basierend auf den Preisvergleichen."""
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


def _print_dcf_fmp(ticker, mos_percent=0.25):
    """
    Prints a compact DCF-fmp report to stdout for the given ticker.
    """
    data = get_dcf_fmp(ticker, mos_percent)
    t = data["ticker"]

    print(f"\n==== {t} DCF (current) ====\n")
    if data["dcf"] is None:
        print("DCF: N/A")
    else:
        extra = f" (as of {data['as_of']})" if data.get("as_of") else ""
        print(f"Fair Value: ${data['dcf']:,.2f}{extra}")
        print(f"Buy Price ({int(mos_percent * 100)}% MOS): ${data['buy_price']:,.2f}")

    if data.get("stock_price") is not None:
        print(f"Stock Price: ${data['stock_price']:,.2f}")

        if data.get("price_vs_fair"):
            print(f"vs Fair Value: {data['price_vs_fair']}")
        if data.get("price_vs_buy"):
            print(f"vs Buy Price: {data['price_vs_buy']}")
        if data.get("investment_recommendation"):
            print(f"Recommendation: {data['investment_recommendation']}")

    print()  # trailing newline


if __name__ == "__main__":
    # quick manual test
    _print_dcf_fmp("AAPL", 0.30)
