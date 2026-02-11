"""
Performance Metrics Calculator
Standard financial metrics for strategy evaluation
"""

import numpy as np
import pandas as pd
from typing import List, Dict


class PerformanceMetrics:
    """Calculate standard performance metrics"""

    @staticmethod
    def sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
        """
        Calculate annualized Sharpe Ratio

        Args:
            returns: List of returns (daily/monthly)
            risk_free_rate: Annual risk-free rate (default 2%)

        Returns:
            Sharpe ratio (annualized)
        """
        if len(returns) < 2:
            return 0.0

        returns_array = np.array(returns)
        excess_returns = returns_array - (risk_free_rate / 252)  # Daily risk-free

        if np.std(excess_returns) == 0:
            return 0.0

        sharpe = np.mean(excess_returns) / np.std(excess_returns)
        return sharpe * np.sqrt(252)  # Annualize

    @staticmethod
    def sortino_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
        """
        Calculate annualized Sortino Ratio (downside deviation only)
        """
        if len(returns) < 2:
            return 0.0

        returns_array = np.array(returns)
        excess_returns = returns_array - (risk_free_rate / 252)

        # Only negative returns for downside deviation
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0 or np.std(downside_returns) == 0:
            return 0.0

        sortino = np.mean(excess_returns) / np.std(downside_returns)
        return sortino * np.sqrt(252)

    @staticmethod
    def max_drawdown(portfolio_values: List[float]) -> Dict:
        """
        Calculate maximum drawdown

        Returns:
            Dict with max_drawdown (%), peak_value, trough_value, duration
        """
        if len(portfolio_values) < 2:
            return {"max_drawdown": 0.0, "peak": 0, "trough": 0, "duration": 0}

        values = np.array(portfolio_values)

        # Calculate running maximum
        running_max = np.maximum.accumulate(values)

        # Calculate drawdown at each point
        drawdown = (values - running_max) / running_max

        # Find maximum drawdown
        max_dd = np.min(drawdown)
        max_dd_idx = np.argmin(drawdown)

        # Find peak before max drawdown
        peak_idx = np.argmax(running_max[: max_dd_idx + 1])

        return {
            "max_drawdown": max_dd * 100,  # Percentage
            "peak_value": values[peak_idx],
            "trough_value": values[max_dd_idx],
            "peak_date": peak_idx,
            "trough_date": max_dd_idx,
            "duration_days": max_dd_idx - peak_idx,
        }

    @staticmethod
    def calmar_ratio(annual_return: float, max_drawdown: float) -> float:
        """
        Calmar Ratio = Annual Return / Max Drawdown

        Higher is better (more return per unit of max drawdown)
        """
        if max_drawdown == 0:
            return 0.0
        return annual_return / abs(max_drawdown)

    @staticmethod
    def calculate_all_metrics(
        portfolio_values: List[float],
        trades: List[Dict],
        starting_value: float,
        years: float,
    ) -> Dict:
        """
        Calculate all performance metrics

        Args:
            portfolio_values: Daily portfolio values
            trades: List of closed trades
            starting_value: Initial portfolio value
            years: Investment period in years

        Returns:
            Dict with all metrics
        """
        # Calculate returns
        values = np.array(portfolio_values)
        daily_returns = np.diff(values) / values[:-1]

        # Total return
        final_value = values[-1]
        total_return = ((final_value / starting_value) - 1) * 100

        # CAGR
        cagr = (((final_value / starting_value) ** (1 / years)) - 1) * 100

        # Sharpe & Sortino
        sharpe = PerformanceMetrics.sharpe_ratio(daily_returns)
        sortino = PerformanceMetrics.sortino_ratio(daily_returns)

        # Drawdown
        dd_info = PerformanceMetrics.max_drawdown(portfolio_values)

        # Calmar
        calmar = PerformanceMetrics.calmar_ratio(cagr, dd_info["max_drawdown"])

        # Trade statistics
        if len(trades) > 0:
            wins = sum(1 for t in trades if t["is_win"])
            losses = len(trades) - wins
            win_rate = (wins / len(trades)) * 100

            total_pnl = sum(t["pnl"] for t in trades)

            winning_trades = [t for t in trades if t["is_win"]]
            losing_trades = [t for t in trades if not t["is_win"]]

            avg_win = (
                sum(t["pnl"] for t in winning_trades) / len(winning_trades)
                if winning_trades
                else 0
            )
            avg_loss = (
                sum(t["pnl"] for t in losing_trades) / len(losing_trades)
                if losing_trades
                else 0
            )

            profit_factor = (
                abs(avg_win * wins / (avg_loss * losses))
                if losses > 0 and avg_loss != 0
                else 0
            )

            # Average hold time
            hold_times = []
            for trade in trades:
                buy_date = pd.to_datetime(trade["buy_date"])
                sell_date = pd.to_datetime(trade["sell_date"])
                days = (sell_date - buy_date).days
                hold_times.append(days)

            avg_hold_time = np.mean(hold_times) if hold_times else 0
        else:
            wins = losses = win_rate = total_pnl = 0
            avg_win = avg_loss = profit_factor = avg_hold_time = 0

        return {
            "total_return": total_return,
            "cagr": cagr,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "max_drawdown": dd_info["max_drawdown"],
            "calmar_ratio": calmar,
            "total_trades": len(trades),
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "avg_hold_time_days": avg_hold_time,
            "total_pnl": total_pnl,
        }
