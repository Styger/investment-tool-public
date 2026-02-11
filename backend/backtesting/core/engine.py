"""
Core Backtesting Engine
Reusable backtest runner for different strategies
"""

import backtrader as bt
from datetime import datetime
from typing import List, Type
from .broker_config import configure_broker
from ..data.feeds import FMPDataFeed
from ..data.loaders import load_historical_data


def run_backtest(
    strategy_class: Type[bt.Strategy],
    universe: List[str],
    from_date: datetime,
    to_date: datetime,
    starting_cash: float = 100000.0,
    commission: float = 0.001,
    strategy_params: dict = None,
    verbose: bool = True,
):
    """
    Generic backtest runner

    Args:
        strategy_class: Backtrader Strategy class
        universe: List of ticker symbols
        from_date: Start date
        to_date: End date
        starting_cash: Initial capital
        commission: Commission rate
        strategy_params: Dict of strategy parameters
        verbose: Print progress

    Returns:
        Dict with results
    """
    if verbose:
        print(f"Running backtest: {strategy_class.__name__}")
        print(f"Universe: {len(universe)} stocks")
        print(f"Period: {from_date.date()} to {to_date.date()}")

    # Create Cerebro
    cerebro = bt.Cerebro()

    # Add strategy
    if strategy_params:
        cerebro.addstrategy(strategy_class, **strategy_params)
    else:
        cerebro.addstrategy(strategy_class)

    # Load data
    loaded = 0
    for ticker in universe:
        try:
            df = load_historical_data(ticker, from_date, to_date)
            if df is not None and len(df) > 0:
                data = FMPDataFeed(dataname=df)
                data._name = ticker
                cerebro.adddata(data, name=ticker)
                loaded += 1
                if verbose:
                    print(f"  ✅ {ticker}: {len(df)} days")
        except Exception as e:
            if verbose:
                print(f"  ❌ {ticker}: {e}")

    if loaded == 0:
        raise ValueError("No data loaded")

    # Configure broker
    configure_broker(cerebro, starting_cash, commission, force_fills=True)

    # Run
    start_value = cerebro.broker.getvalue()
    cerebro.run()
    final_value = cerebro.broker.getvalue()

    # Calculate metrics
    profit = final_value - start_value
    profit_pct = (profit / start_value) * 100
    years = (to_date - from_date).days / 365.25
    cagr = (((final_value / start_value) ** (1 / years)) - 1) * 100

    return {
        "start_value": start_value,
        "final_value": final_value,
        "profit": profit,
        "return_pct": profit_pct,
        "cagr": cagr,
        "years": years,
        "loaded_stocks": loaded,
    }
