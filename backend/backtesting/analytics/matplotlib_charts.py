"""
Matplotlib Chart Generator for Reports
Pure Python - no browser dependencies!
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime
from typing import List, Dict
import tempfile
import calendar


class MatplotlibChartGenerator:
    """Generate matplotlib charts for PDF/PowerPoint export"""

    @staticmethod
    def create_equity_curve(
        dates: List,
        portfolio_values: List,
        benchmark_values: List = None,
    ) -> str:
        """
        Create equity curve chart

        Returns: Path to temporary PNG file
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        # Plot strategy (blue - same as web UI)
        ax.plot(
            dates,
            portfolio_values,
            linewidth=2.5,
            label="Strategy",
            color="#1f77b4",
            zorder=3,
        )

        # Plot benchmark if available (purple - same as web UI)
        if benchmark_values and len(benchmark_values) == len(dates):
            ax.plot(
                dates,
                benchmark_values,
                linewidth=2.5,
                label="S&P 500",
                color="#9467bd",
                linestyle="-",
                alpha=1.0,
                zorder=2,
            )

        # Formatting
        ax.set_xlabel("Date", fontsize=12, fontweight="bold")
        ax.set_ylabel("Portfolio Value ($)", fontsize=12, fontweight="bold")
        ax.set_title("Equity Curve", fontsize=16, fontweight="bold", pad=20)
        ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
        ax.legend(loc="upper left", fontsize=11, framealpha=0.9)

        # Format y-axis with commas
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.xticks(rotation=45, ha="right")

        # Style
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        plt.tight_layout()

        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        plt.savefig(
            temp_file.name,
            dpi=150,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        plt.close(fig)

        return temp_file.name

    @staticmethod
    def create_drawdown_chart(dates: List, drawdown_values: List) -> str:
        """
        Create drawdown chart

        Returns: Path to temporary PNG file
        """
        fig, ax = plt.subplots(figsize=(12, 4))

        # Fill drawdown area
        ax.fill_between(
            dates, drawdown_values, 0, color="#d62728", alpha=0.3, label="Drawdown"
        )
        ax.plot(dates, drawdown_values, linewidth=1.5, color="#8b0000", zorder=3)

        # Formatting
        ax.set_xlabel("Date", fontsize=12, fontweight="bold")
        ax.set_ylabel("Drawdown (%)", fontsize=12, fontweight="bold")
        ax.set_title("Drawdown Over Time", fontsize=16, fontweight="bold", pad=20)
        ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
        ax.axhline(y=0, color="black", linestyle="-", linewidth=0.8)

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.xticks(rotation=45, ha="right")

        # Style
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        plt.tight_layout()

        # Save
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        plt.savefig(
            temp_file.name,
            dpi=150,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        plt.close(fig)

        return temp_file.name

    @staticmethod
    def create_monthly_returns_heatmap(
        dates: List,
        portfolio_values: List,
    ) -> str:
        """
        Create monthly returns heatmap

        Returns: Path to temporary PNG file
        """
        # Calculate monthly returns
        monthly_returns = MatplotlibChartGenerator._calculate_monthly_returns(
            dates, portfolio_values
        )

        if not monthly_returns:
            # No data - create empty chart
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(
                0.5,
                0.5,
                "Insufficient data for monthly returns",
                ha="center",
                va="center",
                fontsize=14,
            )
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            plt.savefig(temp_file.name, dpi=150, bbox_inches="tight")
            plt.close(fig)
            return temp_file.name

        # Organize by year and month
        years = sorted(set(year for year, _ in monthly_returns.keys()))
        months = list(range(1, 13))

        # Create matrix
        data_matrix = np.full((len(years), 12), np.nan)

        for (year, month), ret in monthly_returns.items():
            year_idx = years.index(year)
            month_idx = month - 1
            data_matrix[year_idx, month_idx] = ret

        # Create heatmap
        fig, ax = plt.subplots(figsize=(12, max(4, len(years) * 0.5)))

        # Color map
        im = ax.imshow(
            data_matrix,
            cmap="RdYlGn",
            aspect="auto",
            vmin=-10,
            vmax=10,
            interpolation="nearest",
        )

        # Colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("Monthly Return (%)", rotation=270, labelpad=20, fontsize=11)

        # Labels
        ax.set_xticks(np.arange(12))
        ax.set_xticklabels([calendar.month_abbr[i] for i in range(1, 13)])
        ax.set_yticks(np.arange(len(years)))
        ax.set_yticklabels(years)

        ax.set_xlabel("Month", fontsize=12, fontweight="bold")
        ax.set_ylabel("Year", fontsize=12, fontweight="bold")
        ax.set_title(
            "Monthly Returns Heatmap (%)", fontsize=16, fontweight="bold", pad=20
        )

        # Add text annotations
        for i in range(len(years)):
            for j in range(12):
                if not np.isnan(data_matrix[i, j]):
                    text = ax.text(
                        j,
                        i,
                        f"{data_matrix[i, j]:.1f}",
                        ha="center",
                        va="center",
                        color="black",
                        fontsize=8,
                        fontweight="bold",
                    )

        plt.tight_layout()

        # Save
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        plt.savefig(
            temp_file.name,
            dpi=150,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        plt.close(fig)

        return temp_file.name

    @staticmethod
    def _calculate_monthly_returns(dates, values):
        """Calculate monthly returns from daily data"""
        if len(dates) < 2:
            return {}

        monthly_returns = {}
        current_month_start_val = values[0]
        current_month = (dates[0].year, dates[0].month)

        for i in range(1, len(dates)):
            date = dates[i]
            month_key = (date.year, date.month)

            if month_key != current_month:
                # Month changed - calculate return
                month_end_val = values[i - 1]
                if current_month_start_val != 0:
                    ret = (
                        (month_end_val - current_month_start_val)
                        / current_month_start_val
                        * 100
                    )
                    monthly_returns[current_month] = ret

                # Start new month
                current_month = month_key
                current_month_start_val = values[i]

        # Last month
        if current_month_start_val != 0:
            ret = (values[-1] - current_month_start_val) / current_month_start_val * 100
            monthly_returns[current_month] = ret

        return monthly_returns

    @staticmethod
    def generate_all_charts(results: Dict) -> Dict[str, str]:
        """
        Generate all charts from backtest results

        Returns: Dict mapping chart names to file paths
        """
        chart_paths = {}

        try:
            # ✅ DEBUG: Print complete results structure
            print("\n" + "=" * 70)
            print("🔍 DEBUG: Checking results structure...")
            print("=" * 70)
            print(f"📋 Top-level keys in results: {list(results.keys())}")
            print()

            # Check benchmark data in detail
            if "benchmark" in results:
                benchmark = results["benchmark"]
                print("📊 BENCHMARK DATA FOUND:")
                print(f"   Keys in benchmark: {list(benchmark.keys())}")
                print()

                for key, value in benchmark.items():
                    if isinstance(value, list):
                        print(f"   ✅ {key}: list with {len(value)} items")
                        if len(value) > 0:
                            print(f"      First value: {value[0]}")
                            print(f"      Last value: {value[-1]}")
                    elif isinstance(value, (int, float)):
                        print(f"   ✅ {key}: {value}")
                    elif isinstance(value, bool):
                        print(f"   ✅ {key}: {value}")
                    else:
                        print(f"   ✅ {key}: {type(value).__name__}")
                print()
            else:
                print("❌ NO 'benchmark' key in results!")
                print()

            dates = results.get("dates", [])
            values = results.get("portfolio_values", [])

            print(f"📅 Dates: {len(dates)} values")
            print(f"💰 Portfolio values: {len(values)} values")

            if not dates or not values:
                print("⚠️  No data available for charts")
                print("=" * 70 + "\n")
                return chart_paths

            # Get benchmark data - try ALL possible locations
            print("\n🔎 Searching for benchmark values...")
            benchmark_data = results.get("benchmark", {})
            benchmark_values = None

            # Try different possible keys
            possible_keys = [
                "benchmark_values",
                "sp500_values",
                "values",
                "benchmark_portfolio_values",
                "portfolio_values",
            ]

            for key in possible_keys:
                if key in benchmark_data:
                    potential_values = benchmark_data[key]
                    # Check if it's array-like (list, ndarray, etc.)
                    if (
                        hasattr(potential_values, "__len__")
                        and len(potential_values) > 0
                    ):
                        # Convert to list if needed
                        if hasattr(potential_values, "tolist"):
                            benchmark_values = potential_values.tolist()
                        else:
                            benchmark_values = list(potential_values)
                        print(
                            f"✅ Found benchmark data in key '{key}': {len(benchmark_values)} values (type: {type(potential_values).__name__})"
                        )
                        break

            if not benchmark_values:
                print("⚠️  No benchmark values found - chart will only show strategy")
                print(f"   Tried keys: {possible_keys}")

            print("=" * 70 + "\n")

            # Equity curve with benchmark
            print("📊 Generating equity curve...")
            chart_paths["equity"] = MatplotlibChartGenerator.create_equity_curve(
                dates, values, benchmark_values
            )

            # Drawdown
            print("📊 Generating drawdown chart...")
            drawdown_values = results.get("drawdown_values", [])
            if drawdown_values:
                chart_paths["drawdown"] = (
                    MatplotlibChartGenerator.create_drawdown_chart(
                        dates, drawdown_values
                    )
                )

            # Monthly returns
            print("📊 Generating monthly returns heatmap...")
            chart_paths["monthly"] = (
                MatplotlibChartGenerator.create_monthly_returns_heatmap(dates, values)
            )

            print(f"✅ Generated {len(chart_paths)} charts successfully!")

        except Exception as e:
            print(f"⚠️  Error generating charts: {e}")
            import traceback

            traceback.print_exc()

        return chart_paths
