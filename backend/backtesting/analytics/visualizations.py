"""
Visualization Module
Generate interactive charts for backtest analysis using Plotly
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class BacktestVisualizer:
    """Generate interactive charts for backtest results"""

    def __init__(self, output_dir: str = "backend/backtesting/results/charts"):
        """
        Initialize visualizer

        Args:
            output_dir: Directory to save charts
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Color scheme
        self.colors = {
            "strategy": "#2E86AB",
            "benchmark": "#A23B72",
            "buy": "#06D6A0",
            "sell": "#EF476F",
            "positive": "#06D6A0",
            "negative": "#EF476F",
        }

    def plot_equity_curve(
        self,
        dates: List[datetime],
        portfolio_values: List[float],
        benchmark_values: Optional[List[float]] = None,
        trades: Optional[List[Dict]] = None,
        title: str = "Portfolio Equity Curve",
        filename: str = "equity_curve",
    ) -> go.Figure:
        """
        Plot portfolio value over time with benchmark comparison

        Args:
            dates: List of dates
            portfolio_values: Portfolio values over time
            benchmark_values: Benchmark values (optional)
            trades: List of trades for markers (optional)
            title: Chart title
            filename: Output filename (without extension)

        Returns:
            Plotly Figure object
        """
        # Convert to pandas for easier handling
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(dates),
                "portfolio": portfolio_values,
                "benchmark": (
                    benchmark_values
                    if benchmark_values is not None
                    else [None] * len(dates)
                ),
            }
        )

        # Normalize to starting value (100)
        starting_value = df["portfolio"].iloc[0]
        df["portfolio_normalized"] = (df["portfolio"] / starting_value) * 100

        if benchmark_values is not None:  # ← WICHTIG: is not None!
            benchmark_start = df["benchmark"].iloc[0]
            df["benchmark_normalized"] = (df["benchmark"] / benchmark_start) * 100

        # Create figure
        fig = go.Figure()

        # Add portfolio line
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["portfolio_normalized"],
                name="Strategy",
                line=dict(color=self.colors["strategy"], width=3),
                mode="lines",
                hovertemplate="<b>Strategy</b><br>"
                + "Date: %{x|%Y-%m-%d}<br>"
                + "Value: %{y:.2f}<br>"
                + "<extra></extra>",
            )
        )

        # Add benchmark line
        if benchmark_values is not None:  # ← WICHTIG: is not None!
            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["benchmark_normalized"],
                    name="S&P 500",
                    line=dict(color=self.colors["benchmark"], width=3, dash="dash"),
                    mode="lines",
                    hovertemplate="<b>S&P 500</b><br>"
                    + "Date: %{x|%Y-%m-%d}<br>"
                    + "Value: %{y:.2f}<br>"
                    + "<extra></extra>",
                )
            )

        # Add trade markers
        if trades:
            buy_dates = []
            buy_values = []
            sell_dates = []
            sell_values = []
            buy_labels = []
            sell_labels = []

            for trade in trades:
                buy_date = pd.to_datetime(trade["buy_date"])
                sell_date = pd.to_datetime(trade["sell_date"])

                # Find closest date in dataframe
                buy_idx = (
                    df[df["date"] >= buy_date].index[0]
                    if any(df["date"] >= buy_date)
                    else None
                )
                sell_idx = (
                    df[df["date"] >= sell_date].index[0]
                    if any(df["date"] >= sell_date)
                    else None
                )

                if buy_idx is not None:
                    buy_dates.append(df.loc[buy_idx, "date"])
                    buy_values.append(df.loc[buy_idx, "portfolio_normalized"])
                    buy_labels.append(
                        f"{trade['ticker']}<br>"
                        f"Buy: ${trade['buy_price']:.2f}<br>"
                        f"Size: {trade['size']}"
                    )

                if sell_idx is not None:
                    # Calculate return percentage
                    cost_basis = trade["buy_price"] * trade["size"]
                    return_pct = (
                        (trade["pnl"] / cost_basis) * 100 if cost_basis > 0 else 0
                    )

                    sell_dates.append(df.loc[sell_idx, "date"])
                    sell_values.append(df.loc[sell_idx, "portfolio_normalized"])
                    sell_labels.append(
                        f"{trade['ticker']}<br>"
                        f"Sell: ${trade['sell_price']:.2f}<br>"
                        f"P&L: ${trade['pnl']:,.0f} ({return_pct:.1f}%)"
                    )

                    sell_labels.append(
                        f"{trade['ticker']}<br>"
                        f"Sell: ${trade['sell_price']:.2f}<br>"
                        f"P&L: ${trade['pnl']:,.0f} ({return_pct:.1f}%)"
                    )

            # Add buy markers
            if buy_dates:
                fig.add_trace(
                    go.Scatter(
                        x=buy_dates,
                        y=buy_values,
                        name="Buy",
                        mode="markers",
                        marker=dict(
                            color=self.colors["buy"],
                            size=12,
                            symbol="triangle-up",
                            line=dict(color="white", width=2),
                        ),
                        text=buy_labels,
                        hovertemplate="<b>BUY</b><br>%{text}<extra></extra>",
                    )
                )

            # Add sell markers
            if sell_dates:
                fig.add_trace(
                    go.Scatter(
                        x=sell_dates,
                        y=sell_values,
                        name="Sell",
                        mode="markers",
                        marker=dict(
                            color=self.colors["sell"],
                            size=12,
                            symbol="triangle-down",
                            line=dict(color="white", width=2),
                        ),
                        text=sell_labels,
                        hovertemplate="<b>SELL</b><br>%{text}<extra></extra>",
                    )
                )

        # Add horizontal line at 100
        fig.add_hline(
            y=100,
            line_dash="dot",
            line_color="gray",
            opacity=0.5,
            annotation_text="Starting Value",
        )

        # Layout
        fig.update_layout(
            title=dict(text=title, font=dict(size=20, color="#1a1a1a")),
            xaxis_title="Date",
            yaxis_title="Portfolio Value (Normalized to 100)",
            hovermode="x unified",
            template="plotly_white",
            height=600,
            font=dict(family="Arial, sans-serif", size=12, color="#1a1a1a"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(255, 255, 255, 0.8)",
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
        )

        # Save as HTML and PNG
        html_path = self.output_dir / f"{filename}.html"
        fig.write_html(html_path)
        print(f"✅ Saved interactive chart: {html_path}")

        try:
            png_path = self.output_dir / f"{filename}.png"
            fig.write_image(png_path, width=1400, height=700)
            print(f"✅ Saved PNG chart: {png_path}")
        except Exception as e:
            print(f"⚠️  Could not save PNG (install kaleido): {e}")

        return fig

    def plot_drawdown(
        self,
        dates: List[datetime],
        portfolio_values: List[float],
        title: str = "Portfolio Drawdown",
        filename: str = "drawdown",
    ) -> go.Figure:
        """
        Plot drawdown chart (underwater plot)

        Args:
            dates: List of dates
            portfolio_values: Portfolio values over time
            title: Chart title
            filename: Output filename (without extension)

        Returns:
            Plotly Figure object
        """
        # Calculate drawdown
        values = np.array(portfolio_values)
        running_max = np.maximum.accumulate(values)
        drawdown = (values - running_max) / running_max * 100

        df = pd.DataFrame(
            {
                "date": pd.to_datetime(dates),
                "drawdown": drawdown,
                "value": values,
                "peak": running_max,
            }
        )

        # Find max drawdown
        max_dd_idx = np.argmin(drawdown)
        max_dd_date = dates[max_dd_idx]
        max_dd_value = drawdown[max_dd_idx]

        # Create figure
        fig = go.Figure()

        # Add drawdown area
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["drawdown"],
                fill="tozeroy",
                name="Drawdown",
                line=dict(color=self.colors["negative"], width=2),
                fillcolor="rgba(239, 71, 111, 0.3)",
                hovertemplate="<b>Drawdown</b><br>"
                + "Date: %{x|%Y-%m-%d}<br>"
                + "Drawdown: %{y:.2f}%<br>"
                + "<extra></extra>",
            )
        )

        # Mark max drawdown
        fig.add_trace(
            go.Scatter(
                x=[max_dd_date],
                y=[max_dd_value],
                mode="markers+text",
                name="Max Drawdown",
                marker=dict(
                    color="red",
                    size=15,
                    symbol="circle",
                    line=dict(color="black", width=2),
                ),
                text=[f"Max DD: {max_dd_value:.2f}%"],
                textposition="top center",
                textfont=dict(size=12, color="red"),
                hovertemplate="<b>Maximum Drawdown</b><br>"
                + "Date: %{x|%Y-%m-%d}<br>"
                + "Drawdown: %{y:.2f}%<br>"
                + "<extra></extra>",
            )
        )

        # Layout
        fig.update_layout(
            title=dict(text=title, font=dict(size=20, color="#1a1a1a")),
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            hovermode="x unified",
            template="plotly_white",
            height=600,
            font=dict(family="Arial, sans-serif", size=12, color="#1a1a1a"),
            showlegend=False,
            plot_bgcolor="white",
            paper_bgcolor="white",
        )

        # Add zero line
        fig.add_hline(y=0, line_dash="solid", line_color="black", line_width=1)

        # Save
        html_path = self.output_dir / f"{filename}.html"
        fig.write_html(html_path)
        print(f"✅ Saved interactive chart: {html_path}")

        try:
            png_path = self.output_dir / f"{filename}.png"
            fig.write_image(png_path, width=1400, height=700)
            print(f"✅ Saved PNG chart: {png_path}")
        except Exception as e:
            print(f"⚠️  Could not save PNG (install kaleido): {e}")

        return fig

    def plot_monthly_returns(
        self,
        dates: List[datetime],
        portfolio_values: List[float],
        title: str = "Monthly Returns Heatmap",
        filename: str = "monthly_returns",
    ) -> go.Figure:
        """
        Plot monthly returns as heatmap

        Args:
            dates: List of dates
            portfolio_values: Portfolio values over time
            title: Chart title
            filename: Output filename (without extension)

        Returns:
            Plotly Figure object
        """
        # Create dataframe
        df = pd.DataFrame({"date": pd.to_datetime(dates), "value": portfolio_values})
        df.set_index("date", inplace=True)

        # Resample to monthly
        monthly = df.resample("ME").last()
        monthly["returns"] = monthly["value"].pct_change() * 100

        # Pivot to year x month matrix
        monthly["year"] = monthly.index.year
        monthly["month"] = monthly.index.month

        pivot = monthly.pivot_table(
            values="returns", index="year", columns="month", aggfunc="first"
        )

        # Create heatmap
        fig = go.Figure(
            data=go.Heatmap(
                z=pivot.values,
                x=[
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                ],
                y=pivot.index.astype(str),
                colorscale="RdYlGn",
                zmid=0,
                text=np.round(pivot.values, 1),
                texttemplate="%{text}%",
                textfont={"size": 10},
                hovertemplate="<b>%{y} %{x}</b><br>Return: %{z:.2f}%<extra></extra>",
                colorbar=dict(title="Return (%)"),
            )
        )

        # Layout
        fig.update_layout(
            title=dict(text=title, font=dict(size=20, color="#1a1a1a")),
            xaxis_title="Month",
            yaxis_title="Year",
            template="plotly_white",
            height=600,
            font=dict(family="Arial, sans-serif", size=12, color="#1a1a1a"),
            plot_bgcolor="white",
            paper_bgcolor="white",
        )

        # Save
        html_path = self.output_dir / f"{filename}.html"
        fig.write_html(html_path)
        print(f"✅ Saved interactive chart: {html_path}")

        try:
            png_path = self.output_dir / f"{filename}.png"
            fig.write_image(png_path, width=1400, height=700)
            print(f"✅ Saved PNG chart: {png_path}")
        except Exception as e:
            print(f"⚠️  Could not save PNG (install kaleido): {e}")

        return fig

    def plot_trade_analysis(
        self,
        trades: List[Dict],
        title: str = "Trade Analysis",
        filename: str = "trade_analysis",
    ) -> go.Figure:
        """
        Plot trade statistics in subplots

        Args:
            trades: List of closed trades
            title: Chart title
            filename: Output filename (without extension)

        Returns:
            Plotly Figure object
        """
        if not trades:
            print("⚠️  No trades to plot")
            return None

        # Create subplots
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Trade P&L Distribution",
                "Win/Loss Ratio",
                "Hold Time Distribution",
                "Returns Distribution",
            ),
            specs=[
                [{"type": "bar"}, {"type": "pie"}],
                [{"type": "histogram"}, {"type": "histogram"}],
            ],
        )

        # 1. P&L Distribution
        pnls = [t["pnl"] for t in trades]
        colors = [
            self.colors["positive"] if p > 0 else self.colors["negative"] for p in pnls
        ]
        tickers = [t["ticker"] for t in trades]

        fig.add_trace(
            go.Bar(
                x=list(range(1, len(pnls) + 1)),
                y=pnls,
                marker_color=colors,
                name="P&L",
                text=[f"{t}<br>${p:,.0f}" for t, p in zip(tickers, pnls)],
                hovertemplate="<b>Trade %{x}</b><br>%{text}<extra></extra>",
            ),
            row=1,
            col=1,
        )

        # 2. Win/Loss Pie
        wins = sum(1 for t in trades if t["is_win"])
        losses = len(trades) - wins

        fig.add_trace(
            go.Pie(
                labels=["Wins", "Losses"],
                values=[wins, losses],
                marker_colors=[self.colors["positive"], self.colors["negative"]],
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percent: %{percent}<extra></extra>",
            ),
            row=1,
            col=2,
        )

        # 3. Hold Time Distribution
        hold_times = []
        for t in trades:
            buy_date = pd.to_datetime(t["buy_date"])
            sell_date = pd.to_datetime(t["sell_date"])
            days = (sell_date - buy_date).days
            hold_times.append(days)

        fig.add_trace(
            go.Histogram(
                x=hold_times,
                nbinsx=20,
                marker_color=self.colors["strategy"],
                name="Hold Time",
                hovertemplate="<b>Hold Time</b><br>Days: %{x}<br>Count: %{y}<extra></extra>",
            ),
            row=2,
            col=1,
        )

        # 4. Returns Distribution
        returns = [
            (t["pnl"] / (t["buy_price"] * t["size"])) * 100
            if (t["buy_price"] * t["size"]) > 0
            else 0
            for t in trades
        ]

        fig.add_trace(
            go.Histogram(
                x=returns,
                nbinsx=20,
                marker_color=self.colors["benchmark"],
                name="Returns",
                hovertemplate="<b>Returns</b><br>Return: %{x:.1f}%<br>Count: %{y}<extra></extra>",
            ),
            row=2,
            col=2,
        )

        # Update axes
        fig.update_xaxes(title_text="Trade #", row=1, col=1)
        fig.update_yaxes(title_text="P&L ($)", row=1, col=1)
        fig.update_xaxes(title_text="Hold Time (days)", row=2, col=1)
        fig.update_yaxes(title_text="Frequency", row=2, col=1)
        fig.update_xaxes(title_text="Return (%)", row=2, col=2)
        fig.update_yaxes(title_text="Frequency", row=2, col=2)

        # Layout
        fig.update_layout(
            title=dict(text=title, font=dict(size=20, color="#1a1a1a")),
            height=800,
            showlegend=False,
            template="plotly_white",
            font=dict(family="Arial, sans-serif", size=12, color="#1a1a1a"),
        )

        # Save
        html_path = self.output_dir / f"{filename}.html"
        fig.write_html(html_path)
        print(f"✅ Saved interactive chart: {html_path}")

        try:
            png_path = self.output_dir / f"{filename}.png"
            fig.write_image(png_path, width=1400, height=900)
            print(f"✅ Saved PNG chart: {png_path}")
        except Exception as e:
            print(f"⚠️  Could not save PNG (install kaleido): {e}")

        return fig

    def generate_all_charts(
        self,
        dates: List[datetime],
        portfolio_values: List[float],
        benchmark_values: Optional[List[float]],
        trades: List[Dict],
        prefix: str = "",
    ) -> Dict[str, go.Figure]:
        """
        Generate all charts at once

        Args:
            dates: List of dates
            portfolio_values: Portfolio values
            benchmark_values: Benchmark values
            trades: Closed trades
            prefix: Filename prefix (e.g., "valuekit_")

        Returns:
            Dict with Plotly Figure objects
        """
        print("\n" + "=" * 70)
        print("GENERATING INTERACTIVE CHARTS")
        print("=" * 70)

        charts = {}

        # Equity curve
        charts["equity"] = self.plot_equity_curve(
            dates=dates,
            portfolio_values=portfolio_values,
            benchmark_values=benchmark_values,
            trades=trades,
            filename=f"{prefix}equity_curve",
        )

        # Drawdown
        charts["drawdown"] = self.plot_drawdown(
            dates=dates, portfolio_values=portfolio_values, filename=f"{prefix}drawdown"
        )

        # Monthly returns
        charts["monthly"] = self.plot_monthly_returns(
            dates=dates,
            portfolio_values=portfolio_values,
            filename=f"{prefix}monthly_returns",
        )

        # Trade analysis
        if trades:
            charts["trades"] = self.plot_trade_analysis(
                trades=trades, filename=f"{prefix}trade_analysis"
            )

        print("=" * 70)
        return charts
