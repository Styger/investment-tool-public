"""
PBT (Payback Time) Calculator for Backtesting
8-Year Payback Period Valuation Method with AUTO CAGR
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.logic.pbt import calculate_pbt_with_comparison


class PBTCalculator:
    """Calculate Payback Time Valuation for backtesting with AUTO CAGR"""

    @staticmethod
    def calculate(strategy, ticker: str):
        """
        Calculate PBT valuation using historical data and AUTO CAGR

        Args:
            strategy: Parent strategy instance
            ticker: Stock ticker

        Returns:
            Dict with PBT valuation or None
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

            # ✅ GET AUTO CAGR from strategy
            growth_rate = strategy.calculate_cagr_for_ticker(ticker)

            # Use backend logic to calculate PBT with AUTO CAGR
            result = calculate_pbt_with_comparison(ticker, max_year, growth_rate)

            if not result:
                strategy.log(
                    f"WARNING: No PBT data available for {ticker} ({max_year})"
                )
                return None

            # Return standardized format
            return {
                "method": "PBT",
                "fair_value": result["fair_value"],
                "buy_price": result["buy_price"],
                "current_price": historical_price,  # Use historical price!
                "fcf_per_share": result["fcf_per_share"],
                "growth_rate_used": growth_rate,  # ✅ Track which CAGR was used
            }

        except Exception as e:
            strategy.log(f"ERROR: Failed to calculate PBT for {ticker}: {e}")
            return None
