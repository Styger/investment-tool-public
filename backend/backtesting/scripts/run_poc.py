"""
Run Proof of Concept Backtest
Simple Buy & Hold strategy to test Backtrader setup
"""

import backtrader as bt
from datetime import datetime
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.backtesting.strategies.buy_and_hold import BuyAndHoldStrategy
from backend.backtesting.data.feeds import FMPDataFeed
from backend.backtesting.data.loaders import load_historical_data
from backend.backtesting.core.broker_config import configure_broker


def run_poc_backtest(
    ticker="AAPL",
    from_year=2020,
    to_year=2023,
    starting_cash=10000.0,
):
    """
    Run simple buy & hold backtest (POC)

    Args:
        ticker: Stock ticker
        from_year: Start year
        to_year: End year
        starting_cash: Initial capital

    Returns:
        Final portfolio value
    """
    print("=" * 70)
    print("BUY & HOLD BACKTEST (POC)")
    print("=" * 70)
    print(f"Ticker: {ticker}")
    print(f"Period: {from_year}-{to_year}")
    print(f"Starting Cash: ${starting_cash:,.2f}")
    print()

    # Create Cerebro
    cerebro = bt.Cerebro()
    cerebro.addstrategy(BuyAndHoldStrategy)

    # Load data
    from_date = datetime(from_year, 1, 1)
    to_date = datetime(to_year, 12, 31)

    print("Loading historical data...")
    df = load_historical_data(ticker, from_date, to_date)

    if df is None or len(df) == 0:
        print(f"❌ No data available for {ticker}")
        return None

    data = FMPDataFeed(dataname=df)
    cerebro.adddata(data)
    print(f"✅ Loaded {len(df)} days of data")

    # Configure broker
    configure_broker(cerebro, starting_cash=starting_cash)

    # Run
    start_value = cerebro.broker.getvalue()
    print(f"\n💰 Starting Portfolio Value: ${start_value:,.2f}")
    print("\nRunning backtest...")

    cerebro.run()

    # Results
    final_value = cerebro.broker.getvalue()
    profit = final_value - start_value
    profit_pct = (profit / start_value) * 100

    years = (to_date - from_date).days / 365.25
    cagr = (((final_value / start_value) ** (1 / years)) - 1) * 100

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Starting Value: ${start_value:,.2f}")
    print(f"Final Value:    ${final_value:,.2f}")
    print(f"Profit:         ${profit:,.2f}")
    print(f"Return:         {profit_pct:.2f}%")
    print(f"CAGR:           {cagr:.2f}%")
    print("=" * 70)

    return final_value


if __name__ == "__main__":
    run_poc_backtest(
        ticker="AAPL",
        from_year=2020,
        to_year=2023,
        starting_cash=10000.0,
    )
