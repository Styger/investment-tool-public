"""
Backtesting Visualization
Professional charts using Plotly
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from pathlib import Path
from datetime import datetime


def create_equity_curve_chart(
    dates,
    portfolio_values,
    trades=None,
    benchmark_values=None,
    title="Portfolio Performance",
    output_file=None,
):
    """
    Create professional equity curve chart with Plotly

    Args:
        dates: List of dates
        portfolio_values: List of portfolio values over time
        trades: Optional dict with 'buy_dates' and 'sell_dates'
        benchmark_values: Optional benchmark values (e.g., S&P 500)
        title: Chart title
        output_file: Save to HTML file (optional)

    Returns:
        Plotly figure
    """
    fig = go.Figure()

    # Main equity curve
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=portfolio_values,
            mode="lines",
            name="Portfolio Value",
            line=dict(color="#2E86AB", width=2.5),
            hovertemplate="<b>Date:</b> %{x}<br><b>Value:</b> $%{y:,.2f}<extra></extra>",
        )
    )

    # Benchmark (if provided)
    if benchmark_values is not None:
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=benchmark_values,
                mode="lines",
                name="Benchmark (S&P 500)",
                line=dict(color="#A23B72", width=2, dash="dash"),
                hovertemplate="<b>Date:</b> %{x}<br><b>Value:</b> $%{y:,.2f}<extra></extra>",
            )
        )

    # Buy signals
    if trades and "buy_dates" in trades:
        buy_dates = trades["buy_dates"]
        buy_values = trades["buy_values"]
        fig.add_trace(
            go.Scatter(
                x=buy_dates,
                y=buy_values,
                mode="markers",
                name="Buy",
                marker=dict(
                    symbol="triangle-up",
                    size=12,
                    color="#06D6A0",
                    line=dict(color="white", width=1),
                ),
                hovertemplate="<b>BUY</b><br>Date: %{x}<br>Price: $%{y:,.2f}<extra></extra>",
            )
        )

    # Sell signals
    if trades and "sell_dates" in trades:
        sell_dates = trades["sell_dates"]
        sell_values = trades["sell_values"]
        fig.add_trace(
            go.Scatter(
                x=sell_dates,
                y=sell_values,
                mode="markers",
                name="Sell",
                marker=dict(
                    symbol="triangle-down",
                    size=12,
                    color="#EF476F",
                    line=dict(color="white", width=1),
                ),
                hovertemplate="<b>SELL</b><br>Date: %{x}<br>Price: $%{y:,.2f}<extra></extra>",
            )
        )

    # Layout
    fig.update_layout(
        title=dict(
            text=title, font=dict(size=24, color="#2C3E50"), x=0.5, xanchor="center"
        ),
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        template="plotly_white",
        hovermode="x unified",
        width=1200,
        height=600,
        font=dict(family="Arial, sans-serif", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor="#E8E8E8"),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor="#E8E8E8", tickformat="$,.0f"),
    )

    # Save to file if specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(str(output_path))
        print(f"   💾 Chart saved to: {output_path}")

    return fig


def create_performance_summary_chart(metrics, output_file=None):
    """
    Create performance metrics summary chart

    Args:
        metrics: Dict with performance metrics (CAGR, Sharpe, Max DD, etc.)
        output_file: Save to HTML file (optional)

    Returns:
        Plotly figure
    """
    # Extract metrics
    metric_names = list(metrics.keys())
    metric_values = list(metrics.values())

    # Create bar chart
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=metric_names,
            y=metric_values,
            marker=dict(
                color=["#2E86AB", "#06D6A0", "#EF476F", "#F18F01", "#A23B72"],
                line=dict(color="white", width=1.5),
            ),
            text=[
                f"{v:.2f}%" if isinstance(v, (int, float)) else v for v in metric_values
            ],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>%{y:.2f}%<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text="Performance Metrics Summary",
            font=dict(size=20, color="#2C3E50"),
            x=0.5,
            xanchor="center",
        ),
        xaxis_title="Metric",
        yaxis_title="Value (%)",
        template="plotly_white",
        width=800,
        height=500,
        showlegend=False,
    )

    # Save to file if specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(str(output_path))
        print(f"   💾 Chart saved to: {output_path}")

    return fig


def show_chart(fig):
    """Display chart in browser"""
    fig.show()


if __name__ == "__main__":
    # Test visualization
    import numpy as np

    # Generate dummy data
    dates = pd.date_range("2020-01-01", "2023-12-31", freq="D")
    portfolio_values = 10000 * (1 + np.random.randn(len(dates)).cumsum() * 0.01)

    # Create chart
    fig = create_equity_curve_chart(
        dates=dates,
        portfolio_values=portfolio_values,
        title="Test Portfolio Performance",
    )

    show_chart(fig)
    print("✅ Visualization test complete!")
