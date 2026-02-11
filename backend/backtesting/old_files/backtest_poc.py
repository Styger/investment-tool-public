"""
Backtesting Proof of Concept
Simple Buy & Hold Strategy using FMP data
"""

import backtrader as bt
import datetime
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.api.fmp_api import get_api_key
import requests


class FMPDataFeed(bt.feeds.PandasData):
    """
    Custom data feed for FMP API
    Converts FMP historical data to Backtrader format
    """

    pass


def fetch_fmp_historical_data(ticker, from_date, to_date):
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


class BuyAndHoldStrategy(bt.Strategy):
    """
    Simple Buy & Hold Strategy
    - Buys on first day
    - Holds until end
    - Tests if Backtrader works
    """

    def __init__(self):
        # Track if we already bought
        self.order = None
        self.bought = False

    def log(self, txt, dt=None):
        """Logging function"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()} {txt}")

    def notify_order(self, order):
        """Called when order is executed"""
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"BUY EXECUTED, Price: ${order.executed.price:.2f}")
            elif order.issell():
                self.log(f"SELL EXECUTED, Price: ${order.executed.price:.2f}")

        self.order = None

    def next(self):
        """Called for each bar (day)"""
        # Only log important events (first day, buy, last day)
        # Don't log every single day

        # Check if we have an order pending
        if self.order:
            return

        # If not bought yet, buy everything
        if not self.bought:
            # Calculate how many shares we can buy
            cash = self.broker.getcash()
            price = self.datas[0].close[0]
            size = int(cash / price * 0.95)  # Use 95% of cash

            self.log(f"BUY CREATE, Price: ${price:.2f}, Size: {size} shares")
            self.order = self.buy(size=size)
            self.bought = True

        # Only log last day
        if len(self) == len(self.data) - 1:
            self.log(f"FINAL DAY - Close: ${self.datas[0].close[0]:.2f}")


def run_backtest_and_return_results(ticker, from_date, to_date, starting_cash=10000.0):
    """
    Run backtest and return results dict (for Streamlit UI)

    Args:
        ticker: Stock ticker
        from_date: Start date (datetime)
        to_date: End date (datetime)
        starting_cash: Initial capital

    Returns:
        dict with all results for visualization
    """
    # Create Cerebro
    cerebro = bt.Cerebro()
    cerebro.addstrategy(BuyAndHoldStrategy)

    # Get data
    df = fetch_fmp_historical_data(ticker, from_date, to_date)
    data = FMPDataFeed(dataname=df)
    cerebro.adddata(data)

    # Configure
    cerebro.broker.setcash(starting_cash)
    cerebro.broker.setcommission(commission=0.001)

    # Run
    cerebro.run()

    # Calculate metrics
    final_value = cerebro.broker.getvalue()
    profit = final_value - starting_cash
    profit_pct = (profit / starting_cash) * 100
    years = (to_date - from_date).days / 365.25
    cagr = (((final_value / starting_cash) ** (1 / years)) - 1) * 100

    # Calculate portfolio values over time
    dates = df.index
    prices = df["close"].values
    buy_price = prices[0]
    shares = int(starting_cash / buy_price * 0.95)
    portfolio_values = shares * prices + (starting_cash - shares * buy_price)

    # Return all data
    return {
        "ticker": ticker,
        "start_date": from_date.date(),
        "end_date": to_date.date(),
        "starting_value": starting_cash,
        "final_value": final_value,
        "profit": profit,
        "return_pct": profit_pct,
        "cagr": cagr,
        "years": years,
        "dates": dates,
        "portfolio_values": portfolio_values,
        "trades": {
            "buy_dates": [dates[0]],
            "buy_values": [starting_cash],
        },
    }


if __name__ == "__main__":
    run_backtest_and_return_results(
        "AAPL",
        from_date=datetime(2020, 1, 1),
        to_date=datetime(2023, 12, 31),
        starting_cash=10000.0,
    )
