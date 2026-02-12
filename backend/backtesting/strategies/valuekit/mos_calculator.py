"""
MOS Calculator Wrapper for Backtesting
Uses existing backend/logic/mos.py with historical data and AUTO CAGR
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.logic.mos import calculate_mos_from_data


class MOSCalculator:
    """Calculate Margin of Safety for backtesting with AUTO CAGR"""

    @staticmethod
    def calculate(strategy, ticker: str):
        """
        Calculate MOS using historical price, fundamentals, and AUTO CAGR

        Args:
            strategy: Parent strategy instance
            ticker: Stock ticker

        Returns:
            Dict with MOS data or None
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

            # Get HISTORICAL price from current bar
            historical_price = float(data_feed.close[0])

            # Get HISTORICAL fundamentals
            fundamentals = strategy.get_fundamentals(ticker)
            if not fundamentals:
                return None

            # ✅ GET AUTO CAGR from strategy
            growth_rate = strategy.calculate_cagr_for_ticker(ticker)

            # Use existing MOS logic with historical data + AUTO CAGR
            result = calculate_mos_from_data(
                ticker=ticker,
                current_price=historical_price,  # Historical!
                income_statement=fundamentals["income_statement"],
                balance_sheet=fundamentals["balance_sheet"],
                cashflow=fundamentals["cashflow"],
                growth_rate=growth_rate,  # ✅ AUTO CAGR!
            )

            # Return simplified format for strategy
            return {
                "mos_percentage": -result[
                    "Percentage Difference"
                ],  # Flip sign: positive = undervalued
                "current_price": historical_price,
                "fair_value": result["Fair Value Today"],
                "mos_price": result["MOS Price"],
                "eps_now": result["EPS_now"],
                "recommendation": result["Investment Recommendation"],
                "growth_rate_used": growth_rate,  # ✅ Track which CAGR was used
            }

        except Exception as e:
            strategy.log(f"ERROR: Failed to calculate MOS for {ticker}: {e}")
            return None
