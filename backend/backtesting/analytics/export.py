"""
Export Module
Export backtest results to CSV and Excel
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict
from pathlib import Path


class BacktestExporter:
    """Export backtest results to files"""

    def __init__(self, output_dir: str = "backend/backtesting/results/exports"):
        """
        Initialize exporter

        Args:
            output_dir: Directory to save exports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_trades(
        self,
        trades: List[Dict],
        format: str = "csv",
        filename: str = "trades",
    ) -> str:
        """
        Export trade log to CSV or Excel

        Args:
            trades: List of closed trades
            format: 'csv' or 'excel'
            filename: Output filename (without extension)

        Returns:
            Path to exported file
        """
        if not trades:
            print("⚠️  No trades to export")
            return None

        # Convert to DataFrame
        df = pd.DataFrame(trades)

        # Calculate additional columns
        df["hold_days"] = (
            pd.to_datetime(df["sell_date"]) - pd.to_datetime(df["buy_date"])
        ).dt.days

        df["return_pct"] = (df["pnl"] / (df["buy_price"] * df["size"])) * 100

        # Reorder columns
        columns = [
            "ticker",
            "buy_date",
            "sell_date",
            "hold_days",
            "buy_price",
            "sell_price",
            "size",
            "pnl",
            "return_pct",
            "is_win",
        ]

        # Only include columns that exist
        df = df[[col for col in columns if col in df.columns]]

        # Format
        df["buy_date"] = pd.to_datetime(df["buy_date"]).dt.date
        df["sell_date"] = pd.to_datetime(df["sell_date"]).dt.date
        df["buy_price"] = df["buy_price"].round(2)
        df["sell_price"] = df["sell_price"].round(2)
        df["pnl"] = df["pnl"].round(2)
        df["return_pct"] = df["return_pct"].round(2)

        # Save
        if format.lower() == "excel":
            output_path = self.output_dir / f"{filename}.xlsx"
            df.to_excel(output_path, index=False, engine="openpyxl")
        else:
            output_path = self.output_dir / f"{filename}.csv"
            df.to_csv(output_path, index=False)

        print(f"✅ Exported trades to: {output_path}")
        return str(output_path)

    def export_metrics(
        self,
        metrics: Dict,
        benchmark: Dict,
        format: str = "csv",
        filename: str = "metrics",
    ) -> str:
        """
        Export performance metrics to CSV or Excel

        Args:
            metrics: Performance metrics dict
            benchmark: Benchmark comparison dict
            format: 'csv' or 'excel'
            filename: Output filename (without extension)

        Returns:
            Path to exported file
        """
        # Combine metrics
        data = {
            "Metric": [],
            "Value": [],
            "Unit": [],
        }

        # Strategy metrics
        data["Metric"].append("Total Return")
        data["Value"].append(f"{metrics['total_return']:.2f}")
        data["Unit"].append("%")

        data["Metric"].append("CAGR")
        data["Value"].append(f"{metrics['cagr']:.2f}")
        data["Unit"].append("%")

        data["Metric"].append("Sharpe Ratio")
        data["Value"].append(f"{metrics['sharpe_ratio']:.2f}")
        data["Unit"].append("")

        data["Metric"].append("Sortino Ratio")
        data["Value"].append(f"{metrics['sortino_ratio']:.2f}")
        data["Unit"].append("")

        data["Metric"].append("Max Drawdown")
        data["Value"].append(f"{metrics['max_drawdown']:.2f}")
        data["Unit"].append("%")

        data["Metric"].append("Calmar Ratio")
        data["Value"].append(f"{metrics['calmar_ratio']:.2f}")
        data["Unit"].append("")

        data["Metric"].append("Win Rate")
        data["Value"].append(f"{metrics['win_rate']:.1f}")
        data["Unit"].append("%")

        data["Metric"].append("Profit Factor")
        data["Value"].append(f"{metrics['profit_factor']:.2f}")
        data["Unit"].append("")

        data["Metric"].append("Avg Hold Time")
        data["Value"].append(f"{metrics['avg_hold_time_days']:.0f}")
        data["Unit"].append("days")

        data["Metric"].append("Total Trades")
        data["Value"].append(f"{metrics['total_trades']}")
        data["Unit"].append("")

        # Benchmark comparison
        if benchmark.get("benchmark_available"):
            data["Metric"].append("")
            data["Value"].append("")
            data["Unit"].append("")

            data["Metric"].append("Benchmark Return (S&P 500)")
            data["Value"].append(f"{benchmark['benchmark_return']:.2f}")
            data["Unit"].append("%")

            data["Metric"].append("Benchmark CAGR")
            data["Value"].append(f"{benchmark['benchmark_cagr']:.2f}")
            data["Unit"].append("%")

            data["Metric"].append("Outperformance")
            data["Value"].append(f"{benchmark['outperformance']:+.2f}")
            data["Unit"].append("%")

            data["Metric"].append("Alpha")
            data["Value"].append(f"{benchmark['alpha']:+.2f}")
            data["Unit"].append("%")

            data["Metric"].append("Beta")
            data["Value"].append(f"{benchmark['beta']:.2f}")
            data["Unit"].append("")

            data["Metric"].append("Correlation")
            data["Value"].append(f"{benchmark['correlation']:.2f}")
            data["Unit"].append("")

            data["Metric"].append("Information Ratio")
            data["Value"].append(f"{benchmark['information_ratio']:.2f}")
            data["Unit"].append("")

        df = pd.DataFrame(data)

        # Save
        if format.lower() == "excel":
            output_path = self.output_dir / f"{filename}.xlsx"
            df.to_excel(output_path, index=False, engine="openpyxl")
        else:
            output_path = self.output_dir / f"{filename}.csv"
            df.to_csv(output_path, index=False)

        print(f"✅ Exported metrics to: {output_path}")
        return str(output_path)

    def export_portfolio_values(
        self,
        dates: List[datetime],
        portfolio_values: List[float],
        benchmark_values: List[float] = None,
        format: str = "csv",
        filename: str = "portfolio_values",
    ) -> str:
        """
        Export daily portfolio values to CSV or Excel

        Args:
            dates: List of dates
            portfolio_values: Portfolio values
            benchmark_values: Benchmark values (optional)
            format: 'csv' or 'excel'
            filename: Output filename (without extension)

        Returns:
            Path to exported file
        """
        data = {
            "date": dates,
            "portfolio_value": portfolio_values,
        }

        if benchmark_values is not None:
            data["benchmark_value"] = benchmark_values

        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["portfolio_value"] = df["portfolio_value"].round(2)

        if benchmark_values is not None:
            df["benchmark_value"] = df["benchmark_value"].round(2)

        # Save
        if format.lower() == "excel":
            output_path = self.output_dir / f"{filename}.xlsx"
            df.to_excel(output_path, index=False, engine="openpyxl")
        else:
            output_path = self.output_dir / f"{filename}.csv"
            df.to_csv(output_path, index=False)

        print(f"✅ Exported portfolio values to: {output_path}")
        return str(output_path)

    def export_all(
        self,
        dates: List[datetime],
        portfolio_values: List[float],
        benchmark_values: List[float],
        trades: List[Dict],
        metrics: Dict,
        benchmark: Dict,
        prefix: str = "",
        format: str = "csv",
    ) -> Dict[str, str]:
        """
        Export all data at once

        Args:
            dates: List of dates
            portfolio_values: Portfolio values
            benchmark_values: Benchmark values
            trades: Closed trades
            metrics: Performance metrics
            benchmark: Benchmark comparison
            prefix: Filename prefix (e.g., "valuekit_")
            format: 'csv' or 'excel'

        Returns:
            Dict with export paths
        """
        print("\n" + "=" * 70)
        print(f"EXPORTING DATA ({format.upper()})")
        print("=" * 70)

        exports = {}

        # Export trades
        if trades:
            exports["trades"] = self.export_trades(
                trades=trades, format=format, filename=f"{prefix}trades"
            )

        # Export metrics
        exports["metrics"] = self.export_metrics(
            metrics=metrics,
            benchmark=benchmark,
            format=format,
            filename=f"{prefix}metrics",
        )

        # Export portfolio values
        exports["portfolio"] = self.export_portfolio_values(
            dates=dates,
            portfolio_values=portfolio_values,
            benchmark_values=benchmark_values,
            format=format,
            filename=f"{prefix}portfolio_values",
        )

        print("=" * 70)
        return exports
