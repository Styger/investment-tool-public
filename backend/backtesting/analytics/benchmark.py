"""
Benchmark Comparison
Compare strategy performance against market benchmarks (S&P 500)
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.backtesting.data.loaders import load_historical_data


class BenchmarkComparison:
    """Compare strategy performance against benchmarks"""

    @staticmethod
    def load_spy_benchmark(from_date: datetime, to_date: datetime) -> pd.DataFrame:
        """
        Load S&P 500 (SPY) data for benchmark comparison

        Args:
            from_date: Start date
            to_date: End date

        Returns:
            DataFrame with SPY prices
        """
        try:
            df = load_historical_data("SPY", from_date, to_date)
            return df
        except Exception as e:
            print(f"Warning: Could not load SPY benchmark data: {e}")
            return None

    @staticmethod
    def calculate_benchmark_returns(
        benchmark_df: pd.DataFrame, starting_value: float
    ) -> Dict:
        """
        Calculate buy & hold returns for benchmark

        Args:
            benchmark_df: Benchmark price data
            starting_value: Initial investment amount

        Returns:
            Dict with benchmark performance
        """
        if benchmark_df is None or len(benchmark_df) == 0:
            return None

        first_price = benchmark_df.iloc[0]["close"]
        last_price = benchmark_df.iloc[-1]["close"]

        shares = starting_value / first_price
        final_value = shares * last_price

        total_return = ((final_value / starting_value) - 1) * 100

        # Calculate CAGR
        days = len(benchmark_df)
        years = days / 365.25
        cagr = (((final_value / starting_value) ** (1 / years)) - 1) * 100

        # Calculate portfolio values over time
        portfolio_values = (benchmark_df["close"] * shares).values

        # Calculate daily returns
        daily_returns = benchmark_df["close"].pct_change().dropna().values

        return {
            "starting_value": starting_value,
            "final_value": final_value,
            "total_return": total_return,
            "cagr": cagr,
            "portfolio_values": portfolio_values,
            "daily_returns": daily_returns,
        }

    @staticmethod
    def calculate_alpha_beta(
        strategy_returns: List[float],
        benchmark_returns: List[float],
        risk_free_rate: float = 0.02,
    ) -> Dict:
        """
        Calculate Alpha and Beta

        Args:
            strategy_returns: Daily returns of strategy
            benchmark_returns: Daily returns of benchmark
            risk_free_rate: Annual risk-free rate

        Returns:
            Dict with alpha, beta, correlation
        """
        if len(strategy_returns) != len(benchmark_returns):
            # Align lengths
            min_len = min(len(strategy_returns), len(benchmark_returns))
            strategy_returns = strategy_returns[:min_len]
            benchmark_returns = benchmark_returns[:min_len]

        strat_returns = np.array(strategy_returns)
        bench_returns = np.array(benchmark_returns)

        # Calculate beta (covariance / variance)
        covariance = np.cov(strat_returns, bench_returns)[0, 1]
        benchmark_variance = np.var(bench_returns)

        if benchmark_variance == 0:
            beta = 0
        else:
            beta = covariance / benchmark_variance

        # Calculate alpha (annualized)
        daily_rf = risk_free_rate / 252
        strat_excess = strat_returns - daily_rf
        bench_excess = bench_returns - daily_rf

        alpha_daily = np.mean(strat_excess) - beta * np.mean(bench_excess)
        alpha_annual = alpha_daily * 252 * 100  # Annualized percentage

        # Correlation
        correlation = np.corrcoef(strat_returns, bench_returns)[0, 1]

        # Information Ratio
        tracking_error = np.std(strat_returns - bench_returns) * np.sqrt(252)
        if tracking_error == 0:
            information_ratio = 0
        else:
            information_ratio = alpha_annual / (tracking_error * 100)

        return {
            "alpha": alpha_annual,
            "beta": beta,
            "correlation": correlation,
            "information_ratio": information_ratio,
            "tracking_error": tracking_error * 100,
        }

    @staticmethod
    def compare_with_benchmark(
        strategy_metrics: Dict,
        strategy_returns: List[float],
        from_date: datetime,
        to_date: datetime,
        starting_value: float,
    ) -> Dict:
        """
        Complete benchmark comparison

        Args:
            strategy_metrics: Strategy performance metrics
            strategy_returns: Daily strategy returns
            from_date: Start date
            to_date: End date
            starting_value: Initial capital

        Returns:
            Dict with comparison results
        """
        # Load benchmark
        spy_df = BenchmarkComparison.load_spy_benchmark(from_date, to_date)

        if spy_df is None:
            return {
                "benchmark_available": False,
                "message": "Benchmark data not available",
            }

        # Calculate benchmark returns
        bench_perf = BenchmarkComparison.calculate_benchmark_returns(
            spy_df, starting_value
        )

        # Calculate alpha/beta
        alpha_beta = BenchmarkComparison.calculate_alpha_beta(
            strategy_returns, bench_perf["daily_returns"]
        )

        # Comparison
        outperformance = strategy_metrics["total_return"] - bench_perf["total_return"]
        cagr_diff = strategy_metrics["cagr"] - bench_perf["cagr"]

        return {
            "benchmark_available": True,
            "benchmark_name": "S&P 500 (SPY)",
            "benchmark_return": bench_perf["total_return"],
            "benchmark_cagr": bench_perf["cagr"],
            "benchmark_final_value": bench_perf["final_value"],
            "benchmark_portfolio_values": bench_perf["portfolio_values"],
            "strategy_return": strategy_metrics["total_return"],
            "strategy_cagr": strategy_metrics["cagr"],
            "outperformance": outperformance,
            "cagr_difference": cagr_diff,
            "alpha": alpha_beta["alpha"],
            "beta": alpha_beta["beta"],
            "correlation": alpha_beta["correlation"],
            "information_ratio": alpha_beta["information_ratio"],
            "tracking_error": alpha_beta["tracking_error"],
        }
