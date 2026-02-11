"""
Backtesting Module
Run and visualize backtests directly in ValueKit
"""

import streamlit as st
from ..config import get_text, save_persistence_data, capture_output
from datetime import date, datetime
import sys
from pathlib import Path

# Add backend to path
root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


def show_backtesting_page():
    """Backtesting Analysis Interface with ValueKit Strategy"""
    st.header("📊 ValueKit Backtesting System")
    st.write("Test value investing strategies with historical data")

    # Load persisted values
    persist_data = st.session_state.persist.get("Backtesting", {})

    # Safety check
    if not isinstance(persist_data, dict):
        persist_data = {}

    # Initialize global_ticker if not present
    if "global_ticker" not in st.session_state:
        global_ticker_value = st.session_state.persist.get("global_ticker", "MSFT")
        if isinstance(global_ticker_value, str):
            st.session_state.global_ticker = global_ticker_value
        else:
            st.session_state.global_ticker = "MSFT"

    # ========================================================================
    # CONFIGURATION SECTION
    # ========================================================================
    st.subheader("⚙️ Backtest Configuration")

    col1, col2 = st.columns(2)

    with col1:
        # Universe Selection
        universe_options = {
            "VALUE_3 (3 stocks)": "value_3",
            "VALUE_10 (10 stocks)": "value_10",
            "VALUE_20 (20 stocks)": "value_20",
        }

        selected_universe = st.selectbox(
            "📦 Stock Universe",
            options=list(universe_options.keys()),
            index=0,
            key="backtest_universe",
            help="Select which stocks to backtest. Larger universes take longer.",
        )

        universe_name = universe_options[selected_universe]

    with col2:
        # Initial Capital
        initial_cash = st.number_input(
            "💰 Initial Capital ($)",
            min_value=10000,
            max_value=1000000,
            value=int(persist_data.get("initial_cash", 100000)),
            step=10000,
            key="backtest_initial_cash",
        )

    # Date Range
    col1, col2 = st.columns(2)

    with col1:
        start_year = st.number_input(
            "📅 Start Year",
            min_value=2010,
            max_value=2024,
            value=int(persist_data.get("start_year", 2018)),
            step=1,
            key="backtest_start_year",
        )

    with col2:
        end_year = st.number_input(
            "📅 End Year",
            min_value=2010,
            max_value=2024,
            value=int(persist_data.get("end_year", 2022)),
            step=1,
            key="backtest_end_year",
        )

    # Strategy Parameters
    st.subheader("🎯 Strategy Parameters")

    col1, col2 = st.columns(2)

    with col1:
        mos_threshold = st.slider(
            "📊 Margin of Safety Threshold (%)",
            min_value=0.0,
            max_value=30.0,
            value=float(persist_data.get("mos_threshold", 10.0)),
            step=1.0,
            key="backtest_mos",
            help="Minimum MOS required to buy. Lower = more trades, Higher = fewer trades",
        )

    with col2:
        moat_threshold = st.slider(
            "🏰 Moat Score Threshold (0-50)",
            min_value=0.0,
            max_value=50.0,
            value=float(persist_data.get("moat_threshold", 30.0)),
            step=1.0,
            key="backtest_moat",
            help="Minimum Moat Score required to buy. Lower = more trades, Higher = fewer trades",
        )

    # Info box
    st.info(
        "**📖 Strategy:** ValueKit Value Investing\n\n"
        f"- **Buy when:** MOS > {mos_threshold:.0f}% AND Moat > {moat_threshold:.0f}\n"
        f"- **Sell when:** MOS < -5% OR Moat < 25\n"
        f"- **Position Size:** Equal weight, 95% max allocation\n"
        f"- **Universe:** {selected_universe}"
    )

    # Run Button
    if st.button(
        "🚀 Run Backtest", key="backtest_run", type="primary", use_container_width=True
    ):
        if start_year >= end_year:
            st.error("Start year must be before end year!")
        else:
            with st.spinner(
                f"Running backtest on {selected_universe}... This may take a minute."
            ):
                try:
                    # Save to persistence
                    persist_data = {
                        "initial_cash": str(initial_cash),
                        "start_year": str(start_year),
                        "end_year": str(end_year),
                        "mos_threshold": str(mos_threshold),
                        "moat_threshold": str(moat_threshold),
                        "universe": selected_universe,  # ← ADD to persistence instead!
                    }
                    st.session_state.persist.setdefault("Backtesting", {}).update(
                        persist_data
                    )
                    save_persistence_data()

                    # Import and run ValueKit backtest
                    from backend.backtesting.scripts.run_valuekit import (
                        run_valuekit_backtest,
                    )

                    results = run_valuekit_backtest(
                        universe_name=universe_name,
                        from_year=start_year,
                        to_year=end_year,
                        starting_cash=float(initial_cash),
                        mos_threshold=mos_threshold,
                        moat_threshold=moat_threshold,
                    )

                    # Store results with universe info
                    results["universe_display"] = (
                        selected_universe  # ← ADD to results dict instead!
                    )
                    st.session_state["backtest_results"] = results

                    st.success(f"✅ Backtest complete!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Backtest failed: {str(e)}")
                    import traceback

                    with st.expander("🔍 Error Details"):
                        st.code(traceback.format_exc())

    # ========================================================================
    # RESULTS SECTION
    # ========================================================================
    if "backtest_results" in st.session_state:
        results = st.session_state["backtest_results"]

        st.divider()
        st.header("📈 Backtest Results")

        # ====================================================================
        # KPI METRICS
        # ====================================================================
        st.subheader("💰 Performance Overview")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Final Value",
                f"${results['final_value']:,.2f}",
                delta=f"${results['profit']:,.2f}",
            )

        with col2:
            st.metric("Total Return", f"{results['return_pct']:.2f}%")

        with col3:
            st.metric("CAGR", f"{results['cagr']:.2f}%")

        with col4:
            st.metric(
                "Period", f"{results.get('metrics', {}).get('years', 0):.1f} years"
            )

        # ====================================================================
        # RISK METRICS
        # ====================================================================
        st.subheader("📊 Risk Metrics")

        metrics = results.get("metrics", {})

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Sharpe Ratio",
                f"{metrics.get('sharpe_ratio', 0):.2f}",
                help="Risk-adjusted returns (higher is better)",
            )

        with col2:
            st.metric(
                "Sortino Ratio",
                f"{metrics.get('sortino_ratio', 0):.2f}",
                help="Downside risk-adjusted returns (higher is better)",
            )

        with col3:
            st.metric(
                "Max Drawdown",
                f"{metrics.get('max_drawdown', 0):.2f}%",
                help="Largest peak-to-trough decline",
            )

        with col4:
            st.metric(
                "Calmar Ratio",
                f"{metrics.get('calmar_ratio', 0):.2f}",
                help="Return / Max Drawdown (higher is better)",
            )

        # ====================================================================
        # BENCHMARK COMPARISON
        # ====================================================================
        benchmark = results.get("benchmark", {})

        if benchmark.get("benchmark_available"):
            st.subheader("🎯 vs S&P 500 Benchmark")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                outperf = benchmark.get("outperformance", 0)
                st.metric(
                    "Outperformance",
                    f"{outperf:+.2f}%",
                    delta=f"vs {benchmark.get('benchmark_return', 0):.2f}% S&P 500",
                )

            with col2:
                st.metric(
                    "Alpha",
                    f"{benchmark.get('alpha', 0):+.2f}%",
                    help="Excess return over expected (positive = beating market)",
                )

            with col3:
                st.metric(
                    "Beta",
                    f"{benchmark.get('beta', 0):.2f}",
                    help="Market correlation (< 1 = less volatile than market)",
                )

            with col4:
                st.metric(
                    "Correlation",
                    f"{benchmark.get('correlation', 0):.2f}",
                    help="How closely strategy follows market (0-1)",
                )

        # ====================================================================
        # TRADE STATISTICS
        # ====================================================================
        st.subheader("📝 Trade Statistics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Trades", f"{metrics.get('total_trades', 0)}")

        with col2:
            st.metric("Win Rate", f"{metrics.get('win_rate', 0):.1f}%")

        with col3:
            st.metric(
                "Avg Hold Time", f"{metrics.get('avg_hold_time_days', 0):.0f} days"
            )

        with col4:
            profit_factor = metrics.get("profit_factor", 0)
            pf_display = f"{profit_factor:.2f}" if profit_factor < 999 else "∞"
            st.metric(
                "Profit Factor",
                pf_display,
                help="Gross Profit / Gross Loss (> 1 = profitable)",
            )

        st.divider()

        # ====================================================================
        # CHARTS
        # ====================================================================
        st.subheader("📈 Performance Charts")

        # Get chart data from results
        charts = results.get("charts", {})

        # DEBUG: Check what charts are available
        # st.write("DEBUG: Available charts:", list(charts.keys()) if charts else "None")  # ← Uncomment to debug

        # Tab for different charts
        tab1, tab2 = st.tabs(["📊 Equity Curve", "📉 Drawdown"])

        with tab1:
            # Display equity curve
            if charts and "equity" in charts and charts["equity"] is not None:
                st.plotly_chart(charts["equity"], use_container_width=True)
            else:
                st.warning(
                    "⚠️ Equity curve not available. Charts are generated during backtest run."
                )

        with tab2:
            # Display drawdown
            if charts and "drawdown" in charts and charts["drawdown"] is not None:
                st.plotly_chart(charts["drawdown"], use_container_width=True)
            else:
                st.warning(
                    "⚠️ Drawdown chart not available. Charts are generated during backtest run."
                )

        # ====================================================================
        # TRADE LOG
        # ====================================================================
        trades = results.get("trades", [])

        if trades:
            with st.expander(f"📋 View Trade Log ({len(trades)} trades)"):
                import pandas as pd

                # Convert to DataFrame
                df = pd.DataFrame(trades)

                # Calculate return_pct if not present
                if "return_pct" not in df.columns:
                    df["return_pct"] = (
                        df["pnl"] / (df["buy_price"] * df["size"])
                    ) * 100

                # Format columns
                df["buy_date"] = pd.to_datetime(df["buy_date"]).dt.date
                df["sell_date"] = pd.to_datetime(df["sell_date"]).dt.date
                df["buy_price"] = df["buy_price"].round(2)
                df["sell_price"] = df["sell_price"].round(2)
                df["pnl"] = df["pnl"].round(2)
                df["return_pct"] = df["return_pct"].round(2)

                # Display
                st.dataframe(
                    df[
                        [
                            "ticker",
                            "buy_date",
                            "sell_date",
                            "buy_price",
                            "sell_price",
                            "size",
                            "pnl",
                            "return_pct",
                        ]
                    ],
                    use_container_width=True,
                )

        # ====================================================================
        # DOWNLOAD OPTIONS
        # ====================================================================
        st.subheader("💾 Download Results")

        col1, col2 = st.columns(2)

        with col1:
            # Download trades CSV
            if trades:
                import pandas as pd

                df = pd.DataFrame(trades)
                csv = df.to_csv(index=False)

                st.download_button(
                    label="📥 Download Trades (CSV)",
                    data=csv,
                    file_name=f"valuekit_trades_{date.today()}.csv",
                    mime="text/csv",
                )

        with col2:
            # Download metrics JSON
            import json

            summary = {
                "strategy": "ValueKit Value Investing",
                "universe": results.get("universe_display", "Unknown"),
                "period": f"{start_year}-{end_year}",
                "parameters": {
                    "mos_threshold": mos_threshold,
                    "moat_threshold": moat_threshold,
                    "starting_cash": initial_cash,
                },
                "performance": {
                    "total_return": results["return_pct"],
                    "cagr": results["cagr"],
                    "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                    "max_drawdown": metrics.get("max_drawdown", 0),
                    "total_trades": metrics.get("total_trades", 0),
                    "win_rate": metrics.get("win_rate", 0),
                },
                "benchmark": {
                    "sp500_return": benchmark.get("benchmark_return", 0),
                    "outperformance": benchmark.get("outperformance", 0),
                    "alpha": benchmark.get("alpha", 0),
                    "beta": benchmark.get("beta", 0),
                },
            }

            st.download_button(
                label="📥 Download Summary (JSON)",
                data=json.dumps(summary, indent=2),
                file_name=f"valuekit_summary_{date.today()}.json",
                mime="application/json",
            )

    else:
        # ====================================================================
        # LANDING PAGE (NO RESULTS YET)
        # ====================================================================
        st.divider()
        st.subheader("📖 Getting Started")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **🎯 How to use:**
            1. Select stock universe (start with VALUE_3)
            2. Set date range and initial capital
            3. Adjust strategy parameters
            4. Click "Run Backtest"
            5. Analyze results and download data
            """)

        with col2:
            st.markdown("""
            **📊 What you'll get:**
            - Performance metrics & risk analysis
            - S&P 500 benchmark comparison
            - Interactive charts
            - Detailed trade log
            - Downloadable results
            """)

        st.divider()

        st.info("""
        **💡 Tips:**
        - **MOS Threshold:** Lower values (5-10%) = more trades, Higher values (15-20%) = fewer but "safer" trades
        - **Moat Threshold:** 25-30 is balanced, 35+ is very conservative
        - **Universe:** Start small (VALUE_3), then expand (VALUE_10, VALUE_20)
        - **Time Period:** Longer periods (5+ years) give more reliable results
        """)
