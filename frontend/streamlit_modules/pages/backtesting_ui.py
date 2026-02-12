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
            "SP_100 (100 stocks)": "sp_100",
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

    # ========================================================================
    # VALUATION METHODS
    # ========================================================================
    st.subheader("📊 Valuation Methods")
    st.markdown(
        "**Select which valuation methods to combine for consensus fair value:**"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        use_dcf = st.checkbox(
            "✅ DCF",
            value=persist_data.get("use_dcf", "true").lower() == "true",
            key="backtest_use_dcf",
            help="Discounted Cash Flow - Graham's intrinsic value method",
        )

    with col2:
        use_pbt = st.checkbox(
            "✅ PBT",
            value=persist_data.get("use_pbt", "true").lower() == "true",
            key="backtest_use_pbt",
            help="Payback Time - 8-year payback period valuation",
        )

    with col3:
        use_tencap = st.checkbox(
            "✅ TEN CAP",
            value=persist_data.get("use_tencap", "true").lower() == "true",
            key="backtest_use_tencap",
            help="TEN CAP - Owner earnings valuation method",
        )

    # Warning if no methods selected
    if not (use_dcf or use_pbt or use_tencap):
        st.error("⚠️ Please select at least one valuation method!")

    # Show which methods are active
    methods_active = []
    if use_dcf:
        methods_active.append("DCF (Auto CAGR)")
    if use_pbt:
        methods_active.append("PBT (Auto CAGR)")
    if use_tencap:
        methods_active.append("TEN CAP")

    methods_str = " + ".join(methods_active) if methods_active else "None"

    st.info(
        f"**📐 Consensus Valuation:** {methods_str}\n\n"
        f"Fair Value = Average of selected methods\n\n"
        f"💡 CAGR is calculated automatically from 5-year historical data"  # ✅ Add note
    )

    # ========================================================================
    # STRATEGY PARAMETERS
    # ========================================================================
    st.subheader("🎯 Strategy Parameters")

    # Parameter Presets
    st.markdown("**🎨 Quick Presets:**")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "🛡️ Conservative",
            use_container_width=True,
            help="High thresholds = fewer, safer trades",
        ):
            st.session_state["preset_mos"] = 15.0
            st.session_state["preset_moat"] = 35.0
            st.rerun()

    with col2:
        if st.button(
            "⚖️ Balanced",
            use_container_width=True,
            help="Moderate thresholds = balanced approach",
        ):
            st.session_state["preset_mos"] = 10.0
            st.session_state["preset_moat"] = 30.0
            st.rerun()

    with col3:
        if st.button(
            "🚀 Aggressive",
            use_container_width=True,
            help="Low thresholds = more trades, higher risk",
        ):
            st.session_state["preset_mos"] = 5.0
            st.session_state["preset_moat"] = 25.0
            st.rerun()

    st.divider()

    # Advanced Settings (Collapsible)
    with st.expander("⚙️ Advanced Settings", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Sell Thresholds:**")
            st.caption("MOS < -5% OR Moat < 25")
            st.caption("(Currently hardcoded in strategy)")

        with col2:
            st.markdown("**Position Management:**")
            st.caption("Max Positions: 20")
            st.caption("Rebalance: Quarterly (90 days)")
            st.caption("Equal Weight: 95% max allocation")

        st.info(
            "💡 **Coming Soon:** Customizable sell thresholds, position limits, and rebalancing frequency!"
        )

    # Sliders (with preset values)
    col1, col2 = st.columns(2)

    with col1:
        # Get value from preset or persistence
        default_mos = st.session_state.get(
            "preset_mos", float(persist_data.get("mos_threshold", 10.0))
        )

        mos_threshold = st.slider(
            "📊 Margin of Safety Threshold (%)",
            min_value=0.0,
            max_value=30.0,
            value=default_mos,
            step=1.0,
            key="backtest_mos",
            help="Minimum MOS required to buy. Lower = more trades, Higher = fewer trades",
        )

        # Clear preset after use
        if "preset_mos" in st.session_state:
            del st.session_state["preset_mos"]

    with col2:
        # Get value from preset or persistence
        default_moat = st.session_state.get(
            "preset_moat", float(persist_data.get("moat_threshold", 30.0))
        )

        moat_threshold = st.slider(
            "🏰 Moat Score Threshold (0-50)",
            min_value=0.0,
            max_value=50.0,
            value=default_moat,
            step=1.0,
            key="backtest_moat",
            help="Minimum Moat Score required to buy. Lower = more trades, Higher = fewer trades",
        )

        # Clear preset after use
        if "preset_moat" in st.session_state:
            del st.session_state["preset_moat"]

    # Info box with strategy summary
    st.info(
        f"**📖 Strategy:** ValueKit Consensus Valuation\n\n"
        f"- **Valuation:** {methods_str}\n"
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
        elif not (use_dcf or use_pbt or use_tencap):
            st.error("Please select at least one valuation method!")
        else:
            # Create a placeholder for status updates
            status_placeholder = st.empty()
            progress_bar = st.progress(0)

            try:
                # Step 1: Initialize
                status_placeholder.info("🔧 Initializing backtest...")
                progress_bar.progress(10)

                # Save to persistence
                persist_data = {
                    "initial_cash": str(initial_cash),
                    "start_year": str(start_year),
                    "end_year": str(end_year),
                    "mos_threshold": str(mos_threshold),
                    "moat_threshold": str(moat_threshold),
                    "universe": selected_universe,
                    "use_dcf": str(use_dcf),
                    "use_pbt": str(use_pbt),
                    "use_tencap": str(use_tencap),
                }
                st.session_state.persist.setdefault("Backtesting", {}).update(
                    persist_data
                )
                save_persistence_data()

                # Step 2: Loading data
                status_placeholder.info(
                    f"📊 Loading {selected_universe} data ({start_year}-{end_year})..."
                )
                progress_bar.progress(30)

                # Import and run ValueKit backtest
                from backend.backtesting.scripts.run_valuekit import (
                    run_valuekit_backtest,
                )

                # Step 3: Running backtest
                status_placeholder.info("⚙️ Running backtest strategy...")
                progress_bar.progress(50)

                results = run_valuekit_backtest(
                    universe_name=universe_name,
                    from_year=start_year,
                    to_year=end_year,
                    starting_cash=float(initial_cash),
                    mos_threshold=mos_threshold,
                    moat_threshold=moat_threshold,
                    use_dcf=use_dcf,
                    use_pbt=use_pbt,
                    use_tencap=use_tencap,
                )

                # Step 4: Generating reports
                status_placeholder.info("📈 Generating charts and reports...")
                progress_bar.progress(90)

                # Store results with universe info
                results["universe_display"] = selected_universe
                st.session_state["backtest_results"] = results

                # Step 5: Complete
                progress_bar.progress(100)
                status_placeholder.success("✅ Backtest complete!")

                # Small delay to show completion
                import time

                time.sleep(0.5)

                # Clear status
                status_placeholder.empty()
                progress_bar.empty()

                st.rerun()

            except Exception as e:
                progress_bar.empty()
                status_placeholder.error(f"❌ Backtest failed: {str(e)}")

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

        # Show which valuation methods were used
        valuation_methods = results.get("valuation_methods", [])
        if valuation_methods:
            st.caption(f"🔬 Valuation Methods Used: {', '.join(valuation_methods)}")

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

        # Tab for different charts
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "📊 Equity Curve",
                "📉 Drawdown",
                "🔥 Monthly Returns",
                "📈 Trade Analysis",
            ]
        )

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

        with tab3:
            # Display monthly returns heatmap
            if charts and "monthly" in charts and charts["monthly"] is not None:
                st.plotly_chart(charts["monthly"], use_container_width=True)
                st.caption(
                    "💡 Green = positive months, Red = negative months. Darker colors = larger returns."
                )
            else:
                st.warning(
                    "⚠️ Monthly returns heatmap not available. Charts are generated during backtest run."
                )

        with tab4:
            # Display trade analysis
            if charts and "trades" in charts and charts["trades"] is not None:
                st.plotly_chart(charts["trades"], use_container_width=True)
                st.caption(
                    "💡 Top Left: P&L per trade | Top Right: Win/Loss ratio | Bottom: Hold time & returns distribution"
                )
            else:
                st.info(
                    "💡 Trade analysis shows detailed statistics for all closed trades. Run a backtest to see results."
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
                "strategy": "ValueKit Consensus Valuation",
                "universe": results.get("universe_display", "Unknown"),
                "period": f"{start_year}-{end_year}",
                "valuation_methods": valuation_methods,
                "parameters": {
                    "mos_threshold": mos_threshold,
                    "moat_threshold": moat_threshold,
                    "starting_cash": initial_cash,
                    "use_dcf": use_dcf,
                    "use_pbt": use_pbt,
                    "use_tencap": use_tencap,
                    "cagr_method": "Auto (5-year historical)",
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
            2. Choose valuation methods (DCF/PBT/TEN CAP)
            3. Set date range and initial capital
            4. Adjust strategy parameters
            5. Click "Run Backtest"
            6. Analyze results and download data
            """)

        with col2:
            st.markdown("""
            **📊 What you'll get:**
            - Consensus valuation from multiple methods
            - Performance metrics & risk analysis
            - S&P 500 benchmark comparison
            - Interactive charts
            - Detailed trade log
            - Downloadable results
            """)

        st.divider()

        st.info("""
        **💡 Tips:**
        - **Valuation Methods:** More methods = more robust consensus, but requires complete data
        - **MOS Threshold:** Lower values (5-10%) = more trades, Higher values (15-20%) = fewer but "safer" trades
        - **Moat Threshold:** 25-30 is balanced, 35+ is very conservative
        - **Universe:** Start small (VALUE_3), then expand (VALUE_10, VALUE_20)
        - **Time Period:** Longer periods (5+ years) give more reliable results
        """)
