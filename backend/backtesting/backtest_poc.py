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


def run_backtest():
    """Run simple backtest on AAPL using FMP data"""
    print("=" * 70)
    print("BACKTESTING PROOF OF CONCEPT")
    print("Strategy: Buy & Hold AAPL (2020-2023)")
    print("Data Source: FMP API")
    print("=" * 70)

    # Create Cerebro (Backtrader Engine)
    cerebro = bt.Cerebro()

    # Add strategy
    cerebro.addstrategy(BuyAndHoldStrategy)

    # Get data from FMP
    ticker = "AAPL"
    print(f"\n📊 Loading {ticker} data from FMP API...")
    from_date = datetime.datetime(2020, 1, 1)
    to_date = datetime.datetime(2023, 12, 31)

    try:
        df = fetch_fmp_historical_data(ticker, from_date, to_date)

        # Create Backtrader data feed
        data = FMPDataFeed(dataname=df)
        cerebro.adddata(data)

    except Exception as e:
        print(f"\n❌ Error loading data: {e}")
        print("\nPlease check:")
        print("1. FMP API key is configured")
        print("2. Internet connection is working")
        print("3. Ticker symbol is correct")
        return

    # Set starting cash
    starting_cash = 10000.0
    cerebro.broker.setcash(starting_cash)

    # Add commission (0.1% per trade)
    cerebro.broker.setcommission(commission=0.001)

    # Print starting conditions
    print(f"\n💰 Starting Portfolio Value: ${cerebro.broker.getvalue():,.2f}")
    print(f"📅 Period: {from_date.date()} to {to_date.date()}")
    print(f"📊 Data points: {len(df)} days")
    print("\n" + "=" * 70)
    print("RUNNING BACKTEST...")
    print("=" * 70 + "\n")

    # Run backtest
    cerebro.run()

    # Print final results
    final_value = cerebro.broker.getvalue()
    profit = final_value - starting_cash
    profit_pct = (profit / starting_cash) * 100

    # Calculate CAGR (Compound Annual Growth Rate)
    years = (to_date - from_date).days / 365.25
    cagr = (((final_value / starting_cash) ** (1 / years)) - 1) * 100

    print("\n" + "=" * 70)
    print("BACKTEST RESULTS")
    print("=" * 70)
    print(f"Period:         {from_date.date()} to {to_date.date()} ({years:.1f} years)")
    print(f"Starting Value: ${starting_cash:,.2f}")
    print(f"Final Value:    ${final_value:,.2f}")
    print(f"Profit:         ${profit:,.2f}")
    print(f"Return:         {profit_pct:.2f}%")
    print(f"CAGR:           {cagr:.2f}% per year")
    print("=" * 70)

    # 🆕 NEW: Professional Plotly Chart
    print("\n📈 Generating professional equity curve chart...")

    from backend.backtesting.visualization import create_equity_curve_chart, show_chart
    import numpy as np

    # Create realistic equity curve based on AAPL data
    dates = df.index
    prices = df["close"].values

    # Calculate portfolio value over time
    buy_price = prices[0]
    shares = int(starting_cash / buy_price * 0.95)
    portfolio_values = shares * prices

    # Add remaining cash
    remaining_cash = starting_cash - (shares * buy_price)
    portfolio_values = portfolio_values + remaining_cash

    # Create chart
    fig = create_equity_curve_chart(
        dates=dates,
        portfolio_values=portfolio_values,
        trades={
            "buy_dates": [dates[0]],
            "buy_values": [starting_cash],
        },
        title=f"Buy & Hold Strategy - {ticker} ({from_date.year}-{to_date.year})",
        output_file="backend/backtesting/results/equity_curve.html",
    )

    print("   ✅ Chart saved to: backend/backtesting/results/equity_curve.html")
    print("   🌐 Opening interactive chart in browser...")
    show_chart(fig)

    print("\n" + "=" * 70)
    print("✅ MILESTONE 1 COMPLETE!")
    print("=" * 70)
    print("✓ Backtrader works")
    print("✓ FMP data integration works")
    print("✓ Professional charts work")
    print("✓ Ready for Milestone 2: Historical Data Pipeline")
    print("=" * 70)


if __name__ == "__main__":
    run_backtest()
