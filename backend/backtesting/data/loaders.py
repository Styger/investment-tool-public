"""
Data Loading Functions
Fetch and prepare historical data for backtesting
"""

import pandas as pd
import requests
from datetime import datetime
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.api.fmp_api import get_api_key


def load_historical_data(ticker: str, from_date: datetime, to_date: datetime):
    """
    Fetch historical OHLCV data from FMP

    Args:
        ticker: Stock ticker
        from_date: Start date (datetime)
        to_date: End date (datetime)

    Returns:
        pandas DataFrame with OHLCV data
    """
    api_key = get_api_key()

    # Format dates
    from_str = from_date.strftime("%Y-%m-%d")
    to_str = to_date.strftime("%Y-%m-%d")

    # FMP API endpoint
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}"
    params = {"from": from_str, "to": to_str, "apikey": api_key}

    print(f"   Fetching data from {from_str} to {to_str}...")

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    # Extract historical data
    if "historical" not in data:
        raise ValueError(f"No historical data found for {ticker}")

    historical = data["historical"]

    # Convert to pandas DataFrame
    df = pd.DataFrame(historical)

    # Convert date column to datetime
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)

    # Sort by date (ascending)
    df.sort_index(inplace=True)

    # Rename columns to match Backtrader expectations
    df.rename(
        columns={
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
        },
        inplace=True,
    )

    # Select only needed columns
    df = df[["open", "high", "low", "close", "volume"]]

    # ================================================================
    # CRITICAL FIX: Force very high volume for backtesting
    # Without this line, SELL orders only fill 1 share at a time!
    # ================================================================
    print(f"   🔧 Forcing high volume for backtest (was: {df['volume'].iloc[0]:,.0f})")
    df["volume"] = 1_000_000_000  # 1 billion shares per bar
    # ================================================================

    print(f"   ✅ Loaded {len(df)} days of data")

    return df
