"""
Backtest with ValueKit Strategy
Test the value investing strategy on historical data
"""

import backtrader as bt
from datetime import datetime
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.backtesting.valuekit_strategy import ValueKitStrategy
from backend.backtesting.backtest_poc import fetch_fmp_historical_data, FMPDataFeed
from backend.backtesting.stock_universe import get_universe
from backtrader.fillers import FixedSize


def run_valuekit_backtest(
    universe_name="test_10", from_year=2020, to_year=2023, starting_cash=100000.0
):
    """
    Run backtest with ValueKit Strategy

    Args:
        universe_name: Stock universe to test
        from_year: Start year
        to_year: End year
        starting_cash: Initial capital
    """
    print("=" * 70)
    print("VALUEKIT STRATEGY BACKTEST")
    print("=" * 70)

    # Get universe
    universe = get_universe(universe_name)
    print(f"Universe: {universe_name.upper()} ({len(universe)} stocks)")
    print(f"Period: {from_year}-{to_year}")
    print(f"Starting Cash: ${starting_cash:,.0f}")
    print()

    # Create Cerebro
    cerebro = bt.Cerebro()

    # Add strategy
    cerebro.addstrategy(ValueKitStrategy)

    # Load data for each stock
    from_date = datetime(from_year, 1, 1)
    to_date = datetime(to_year, 12, 31)

    print("Loading historical data...")
    loaded = 0

    for ticker in universe:
        try:
            df = fetch_fmp_historical_data(ticker, from_date, to_date)

            if df is None or len(df) == 0:
                print(f"  ⚠️  {ticker}: No data available")
                continue

            # Create data feed
            data = FMPDataFeed(dataname=df)
            data._name = ticker  # Store ticker name
            cerebro.adddata(data, name=ticker)

            loaded += 1
            print(f"  ✅ {ticker}: {len(df)} days")

        except Exception as e:
            print(f"  ❌ {ticker}: Error - {e}")

    print(f"\n✅ Loaded {loaded}/{len(universe)} stocks")

    if loaded == 0:
        print("❌ No data loaded - cannot run backtest")
        return

    # Configure broker
    cerebro.broker.setcash(starting_cash)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission

    # Force full order execution (ignore volume constraints)
    cerebro.broker.set_coo(True)  # Cheat-On-Open
    cerebro.broker.set_coc(True)  # Cheat-On-Close

    # CRITICAL: Force complete order fills
    cerebro.broker.set_filler(FixedSize())
    cerebro.broker.set_coc(True)

    # Print starting value
    start_value = cerebro.broker.getvalue()
    print(f"\n💰 Starting Portfolio Value: ${start_value:,.2f}")

    # Run backtest
    print("\n" + "=" * 70)
    print("RUNNING BACKTEST...")
    print("=" * 70)

    cerebro.run()

    # Print final results
    final_value = cerebro.broker.getvalue()
    profit = final_value - start_value
    profit_pct = (profit / start_value) * 100

    years = (to_date - from_date).days / 365.25
    cagr = (((final_value / start_value) ** (1 / years)) - 1) * 100

    print("\n" + "=" * 70)
    print("BACKTEST RESULTS")
    print("=" * 70)
    print(f"Starting Value: ${start_value:,.2f}")
    print(f"Final Value:    ${final_value:,.2f}")
    print(f"Profit:         ${profit:,.2f}")
    print(f"Return:         {profit_pct:.2f}%")
    print(f"CAGR:           {cagr:.2f}%")
    print("=" * 70)


if __name__ == "__main__":
    # Test with small universe first
    run_valuekit_backtest(
        universe_name="value_3", from_year=2018, to_year=2022, starting_cash=100000.0
    )
