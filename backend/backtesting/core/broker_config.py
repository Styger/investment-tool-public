"""
Broker Configuration for Backtesting
Centralized settings for cash, commission, order execution
"""

import backtrader as bt
from backtrader.fillers import FixedSize


def configure_broker(
    cerebro: bt.Cerebro,
    starting_cash: float = 100000.0,
    commission: float = 0.001,
    force_fills: bool = True,
):
    """
    Configure broker with standard settings

    Args:
        cerebro: Backtrader Cerebro instance
        starting_cash: Initial capital
        commission: Commission rate (0.001 = 0.1%)
        force_fills: Force complete order fills (ignore volume)

    Returns:
        Configured cerebro instance
    """
    # Set cash
    cerebro.broker.setcash(starting_cash)

    # Set commission
    cerebro.broker.setcommission(commission=commission)

    if force_fills:
        # Force full order execution (ignore volume constraints)
        cerebro.broker.set_coo(True)  # Cheat-On-Open
        cerebro.broker.set_coc(True)  # Cheat-On-Close
        cerebro.broker.set_filler(FixedSize())

    return cerebro
