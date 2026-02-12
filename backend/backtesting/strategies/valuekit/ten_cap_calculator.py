"""
TEN CAP Calculator for Backtesting
Owner Earnings Valuation Method
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.logic.tencap import calculate_ten_cap_with_comparison


class TenCapCalculator:
    """Calculate TEN CAP Valuation for backtesting"""

    @staticmethod
    def calculate(strategy, ticker: str):
        """
        Calculate TEN CAP valuation using historical data

        Args:
            strategy: Parent strategy instance
            ticker: Stock ticker

        Returns:
            Dict with TEN CAP valuation or None
        """
        try:
            # Find data feed for this ticker
            data_feed = None
            for data in strategy.datas:
                if data._name == ticker:
                    data_feed = data
                    break

            if data_feed is None:
                strategy.log(f"ERROR: No data feed found for {ticker}")
                return None

            # Get current backtest date
            current_date = data_feed.datetime.date(0)
            current_year = current_date.year

            # For fundamentals, use previous year's data
            max_year = current_year - 1

            # Get HISTORICAL price from current bar
            historical_price = float(data_feed.close[0])

            # Use backend logic to calculate TEN CAP
            # Note: This uses FMP API which is cached by strategy.get_fundamentals()
            result = calculate_ten_cap_with_comparison(ticker, max_year)

            if not result:
                strategy.log(
                    f"WARNING: No TEN CAP data available for {ticker} ({max_year})"
                )
                return None

            # Return standardized format
            return {
                "method": "TEN_CAP",
                "fair_value": result["ten_cap_fair_value"],
                "buy_price": result["ten_cap_buy_price"],
                "current_price": historical_price,  # Use historical price!
                "owner_earnings": result["owner_earnings"],
                "eps": result["earnings_per_share"],
            }

        except Exception as e:
            strategy.log(f"ERROR: Failed to calculate TEN CAP for {ticker}: {e}")
            return None
