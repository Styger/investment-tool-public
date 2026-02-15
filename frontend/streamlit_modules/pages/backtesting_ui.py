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

    # ========================================================================
    # LOAD SAVED STRATEGY
    # ========================================================================
    st.subheader("💾 Load Saved Strategy")

    try:
        from backend.storage.strategy_storage import StrategyStorage

        storage = StrategyStorage()

        # Get actual logged-in user
        current_user = st.session_state.get("username", "default_user")
        strategies = storage.get_strategies(user_id=current_user, include_shared=True)

        if strategies:
            col1, col2 = st.columns([3, 1])

            with col1:
                # Create strategy options
                strategy_options = {}
                for strategy in strategies:
                    # Add shared/private indicator
                    shared_icon = "🌍" if strategy.get("shared") else "📌"

                    # Add performance info
                    perf = ""
                    if strategy.get("backtest_results"):
                        results_summary = strategy["backtest_results"]
                        perf = f" - CAGR: {results_summary.get('cagr', 0):.1f}%, Win: {results_summary.get('win_rate', 0):.0f}%"

                    label = f"{shared_icon} {strategy['name']}{perf}"
                    strategy_options[label] = strategy

                selected_label = st.selectbox(
                    "Select Strategy",
                    options=["-- New Backtest --"] + list(strategy_options.keys()),
                    help="Load a saved strategy to see results instantly",
                )

            with col2:
                st.markdown("<br>", unsafe_allow_html=True)  # Spacing
                if st.button(
                    "🔄 Refresh",
                    help="Reload saved strategies",
                    use_container_width=True,
                ):
                    st.rerun()

            # ✅ GET SELECTED STRATEGY
            selected_strategy = None
            if selected_label != "-- New Backtest --":
                selected_strategy = strategy_options[selected_label]

            # ✅ LOAD & DELETE BUTTONS
            st.divider()

            col1, col2 = st.columns(2)

            with col1:
                load_disabled = selected_label == "-- New Backtest --"
                load_button = st.button(
                    "📥 Load Strategy",
                    type="primary",
                    use_container_width=True,
                    disabled=load_disabled,
                )

            with col2:
                # Only allow delete for user's own strategies
                current_user = st.session_state.get("username", "default_user")

                can_delete = (
                    selected_label != "-- New Backtest --"
                    and selected_strategy is not None
                    and selected_strategy.get("user_id")
                    == current_user  # Check actual user!
                )

                if st.button(
                    "🗑️ Delete",
                    type="secondary",
                    use_container_width=True,
                    disabled=not can_delete,
                    help="Delete this strategy"
                    if can_delete
                    else "Cannot delete shared strategies",
                ):
                    if can_delete:
                        st.session_state["confirm_delete_strategy"] = selected_strategy
                        st.rerun()

            # ✅ DELETE CONFIRMATION DIALOG
            if "confirm_delete_strategy" in st.session_state:
                strategy_to_delete = st.session_state["confirm_delete_strategy"]

                st.divider()
                st.error(f"⚠️ **Confirm Deletion**")
                st.warning(
                    f"Delete strategy: **{strategy_to_delete['name']}**?\n\nThis action cannot be undone!"
                )

                col1, col2, col3 = st.columns([1, 1, 2])

                with col1:
                    if st.button(
                        "✅ Yes, Delete", type="primary", use_container_width=True
                    ):
                        try:
                            from backend.storage.strategy_storage import StrategyStorage

                            storage = StrategyStorage()

                            success = storage.delete_strategy(
                                strategy_id=strategy_to_delete["id"],
                                user_id="default_user",
                            )

                            if success:
                                st.success(f"✅ Deleted '{strategy_to_delete['name']}'")
                                # Clear session state
                                del st.session_state["confirm_delete_strategy"]
                                if "backtest_results" in st.session_state:
                                    del st.session_state["backtest_results"]
                                if "loaded_strategy_name" in st.session_state:
                                    del st.session_state["loaded_strategy_name"]
                                if "loaded_strategy_params" in st.session_state:
                                    del st.session_state["loaded_strategy_params"]

                                import time

                                time.sleep(1)  # Show success message
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete strategy")

                        except Exception as e:
                            st.error(f"❌ Error deleting strategy: {str(e)}")

                with col2:
                    if st.button("❌ Cancel", use_container_width=True):
                        del st.session_state["confirm_delete_strategy"]
                        st.rerun()

            # Load strategy when button clicked
            if load_button and selected_strategy:
                # Restore full results to session state
                if selected_strategy.get("full_results"):
                    # Reconstruct results with charts
                    loaded_results = selected_strategy["full_results"]

                    # Restore charts from JSON
                    if selected_strategy.get("charts_data"):
                        import plotly.graph_objects as go
                        from plotly.io import from_json

                        charts = {}
                        for key, chart_json in selected_strategy["charts_data"].items():
                            if chart_json:
                                charts[key] = from_json(chart_json)
                            else:
                                charts[key] = None

                        loaded_results["charts"] = charts

                    # Restore to session state
                    st.session_state["backtest_results"] = loaded_results
                    st.session_state["loaded_strategy_name"] = selected_strategy["name"]
                    st.session_state["loaded_strategy_params"] = selected_strategy[
                        "parameters"
                    ]

                    st.success(f"✅ Loaded: {selected_strategy['name']}")
                    st.info("📊 Scroll down to see results instantly!")
                    st.rerun()
                else:
                    st.warning(
                        "⚠️ This strategy was saved without full results. Run a new backtest with these parameters."
                    )
                    # Still load parameters
                    st.session_state["loaded_strategy_params"] = selected_strategy[
                        "parameters"
                    ]
                    st.rerun()
        else:
            st.info(
                "💡 No saved strategies yet. Run a backtest and save it to reuse later!"
            )

    except Exception as e:
        st.error(f"❌ Error loading strategies: {str(e)}")

    # Show loaded strategy info
    if "loaded_strategy_name" in st.session_state:
        st.success(
            f"✅ Currently viewing: **{st.session_state['loaded_strategy_name']}**"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Re-Run with Same Parameters"):
                # Parameters are already loaded, just click Run Backtest
                st.info("Parameters loaded! Scroll down and click 'Run Backtest'")

        with col2:
            if st.button("🗑️ Clear Loaded Strategy"):
                # Clear loaded strategy
                if "loaded_strategy_name" in st.session_state:
                    del st.session_state["loaded_strategy_name"]
                if "loaded_strategy_params" in st.session_state:
                    del st.session_state["loaded_strategy_params"]
                if "backtest_results" in st.session_state:
                    del st.session_state["backtest_results"]
                st.rerun()

    st.divider()

    # Load persisted values
    persist_data = st.session_state.persist.get("Backtesting", {})

    # OVERRIDE with loaded strategy params if available
    if "loaded_strategy_params" in st.session_state:
        loaded_params = st.session_state["loaded_strategy_params"]
        persist_data.update(
            {
                "mos_threshold": str(loaded_params.get("mos_threshold", 10.0)),
                "moat_threshold": str(loaded_params.get("moat_threshold", 30.0)),
                "sell_mos_threshold": str(
                    loaded_params.get("sell_mos_threshold", -5.0)
                ),
                "sell_moat_threshold": str(
                    loaded_params.get("sell_moat_threshold", 25.0)
                ),
                "use_mos": str(loaded_params.get("use_mos", True)),
                "use_pbt": str(loaded_params.get("use_pbt", True)),
                "use_tencap": str(loaded_params.get("use_tencap", True)),
                "max_positions": str(loaded_params.get("max_positions", 20)),
                "rebalance_days": str(loaded_params.get("rebalance_days", 90)),
            }
        )

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

    # ========================================================================
    # VALUATION METHODS
    # ========================================================================
    st.subheader("📊 Valuation Methods")
    st.markdown(
        "**Select which valuation methods to combine for consensus fair value:**"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        use_mos = st.checkbox(
            "✅ MOS",
            value=persist_data.get("use_mos", "true").lower() == "true",
            key="backtest_use_mos",
            help="Margin of Safety - Warren Buffett's intrinsic value method",
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
    if not (use_mos or use_pbt or use_tencap):
        st.error("⚠️ Please select at least one valuation method!")

    # Show which methods are active
    methods_active = []
    if use_mos:
        methods_active.append("MOS (Auto CAGR)")
    if use_pbt:
        methods_active.append("PBT (Auto CAGR)")
    if use_tencap:
        methods_active.append("TEN CAP")

    methods_str = " + ".join(methods_active) if methods_active else "None"

    st.info(
        f"**📐 Consensus Valuation:** {methods_str}\n\n"
        f"Fair Value = Average of selected methods\n\n"
        f"💡 CAGR is calculated automatically from 5-year historical data"
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

    # ========================================================================
    # ADVANCED SETTINGS (NOW AFTER MAIN PARAMETERS!)
    # ========================================================================
    with st.expander("⚙️ Advanced Settings", expanded=False):
        st.markdown("### Portfolio Management")

        col1, col2 = st.columns(2)

        with col1:
            # Rebalance Frequency
            rebalance_options = {
                "Monthly (30 days)": 30,
                "Bi-Monthly (60 days)": 60,
                "Quarterly (90 days) ⭐": 90,
                "Semi-Annual (180 days)": 180,
            }

            rebalance_label = st.selectbox(
                "Rebalance Frequency",
                options=list(rebalance_options.keys()),
                index=2,  # Default: Quarterly
                key="backtest_rebalance_freq",
                help="How often to review and rebalance the portfolio. Quarterly is recommended for value investing.",
            )

            rebalance_days = rebalance_options[rebalance_label]

        with col2:
            # Max Positions
            max_positions = st.slider(
                "Max Positions",
                min_value=5,
                max_value=30,
                value=int(persist_data.get("max_positions", 20)),
                step=5,
                key="backtest_max_positions",
                help="Maximum number of stocks to hold simultaneously. Lower = concentrated, Higher = diversified",
            )

        st.divider()

        st.markdown("### Sell Signals")

        col1, col2 = st.columns(2)

        with col1:
            # Sell MOS Threshold
            sell_mos_threshold = st.slider(
                "Sell MOS Threshold (%)",
                min_value=-20.0,
                max_value=0.0,
                value=float(persist_data.get("sell_mos_threshold", -5.0)),
                step=1.0,
                key="backtest_sell_mos",
                help="Sell when MOS falls below this. -5% = sell when overvalued by 5%. More negative = more tolerant.",
            )

        with col2:
            # Sell Moat Threshold
            sell_moat_threshold = st.slider(
                "Sell Moat Threshold (0-50)",
                min_value=0.0,
                max_value=40.0,
                value=float(persist_data.get("sell_moat_threshold", 25.0)),
                step=5.0,
                key="backtest_sell_moat",
                help="Sell when Moat Score falls below this. Lower = more aggressive selling.",
            )

        # ✅ NOW we can safely use mos_threshold and moat_threshold!
        st.info(
            f"**💡 Current Strategy:**\n\n"
            f"- **Buy Signal:** MOS > {mos_threshold}% AND Moat > {moat_threshold}\n"
            f"- **Sell Signal:** MOS < {sell_mos_threshold}% OR Moat < {sell_moat_threshold}\n"
            f"- **Portfolio:** Up to {max_positions} positions, equal weighted\n"
            f"- **Rebalancing:** Every {rebalance_days} days"
        )

        st.caption(
            "💡 Position sizing: Available cash is divided equally among all positions. "
            "⚠️ Lower rebalancing frequencies may show higher returns in backtests "
            "but incur higher transaction costs and taxes in real trading."
        )
    # Run Button
    if st.button(
        "🚀 Run Backtest", key="backtest_run", type="primary", use_container_width=True
    ):
        if start_year >= end_year:
            st.error("Start year must be before end year!")
        elif not (use_mos or use_pbt or use_tencap):
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
                    "use_mos": str(use_mos),
                    "use_pbt": str(use_pbt),
                    "use_tencap": str(use_tencap),
                    "rebalance_days": str(rebalance_days),
                    "max_positions": str(max_positions),
                    "sell_mos_threshold": str(sell_mos_threshold),
                    "sell_moat_threshold": str(sell_moat_threshold),
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
                    use_mos=use_mos,
                    use_pbt=use_pbt,
                    use_tencap=use_tencap,
                    rebalance_days=rebalance_days,
                    max_positions=max_positions,
                    sell_mos_threshold=sell_mos_threshold,
                    sell_moat_threshold=sell_moat_threshold,
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
        # SAVE STRATEGY
        # ====================================================================
        def make_json_serializable(obj):
            """
            Recursively convert numpy arrays, datetime objects, and other non-JSON types to JSON-serializable formats
            """
            import numpy as np
            import pandas as pd
            from datetime import datetime, date

            # ✅ Handle datetime and date objects
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            # Handle numpy types
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, (np.bool_, bool)):
                return bool(obj)
            # Handle pandas types
            elif isinstance(obj, pd.Timestamp):
                return obj.isoformat()
            elif isinstance(obj, pd.Series):
                return obj.tolist()
            elif isinstance(obj, pd.DataFrame):
                return obj.to_dict("records")
            # Handle collections recursively
            elif isinstance(obj, dict):
                return {
                    key: make_json_serializable(value) for key, value in obj.items()
                }
            elif isinstance(obj, list):
                return [make_json_serializable(item) for item in obj]
            elif isinstance(obj, tuple):
                return tuple(make_json_serializable(item) for item in obj)
            # Handle None and primitive types
            elif obj is None or isinstance(obj, (str, int, float)):
                return obj
            # Fallback: try to convert to string
            else:
                try:
                    return str(obj)
                except:
                    return None

        st.divider()
        st.subheader("💾 Save This Strategy")

        st.info(
            "💡 Save this strategy to use in Live Screening. "
            "Screen the S&P 500 with these exact parameters!"
        )

        col1, col2 = st.columns([2, 1])

        with col1:
            if st.button("💾 Save Strategy", type="primary", width="stretch"):
                st.session_state["show_save_modal"] = True

        with col2:
            if st.button("📊 Go to Screening", width="stretch"):
                st.switch_page("pages/screening_ui.py")

        # Save Strategy Modal
        if st.session_state.get("show_save_modal", False):
            with st.form("save_strategy_form"):
                st.markdown("### 💾 Save Strategy")

                strategy_name = st.text_input(
                    "Strategy Name *",
                    placeholder="e.g., Conservative Value, Aggressive Growth",
                    help="Give your strategy a memorable name",
                )

                strategy_description = st.text_area(
                    "Description",
                    placeholder="What makes this strategy unique?",
                    help="Optional: Describe your strategy approach",
                )

                share_strategy = st.checkbox(
                    "🌍 Share with community",
                    value=False,
                    help="Make this strategy visible to other users",
                )

                col1, col2 = st.columns(2)

                with col1:
                    submitted = st.form_submit_button("💾 Save", type="primary")

                with col2:
                    cancelled = st.form_submit_button("Cancel")

                if cancelled:
                    st.session_state["show_save_modal"] = False
                    st.rerun()

                if submitted:
                    if not strategy_name:
                        st.error("⚠️ Please enter a strategy name")
                    else:
                        try:
                            from backend.storage.strategy_storage import StrategyStorage

                            storage = StrategyStorage()

                            # Prepare parameters
                            strategy_params = {
                                "mos_threshold": mos_threshold,
                                "moat_threshold": moat_threshold,
                                "sell_mos_threshold": sell_mos_threshold,
                                "sell_moat_threshold": sell_moat_threshold,
                                "use_mos": use_mos,
                                "use_pbt": use_pbt,
                                "use_tencap": use_tencap,
                                "max_positions": max_positions,
                                "rebalance_days": rebalance_days,
                            }

                            # Prepare backtest results summary
                            backtest_summary = {
                                "return_pct": results["return_pct"],
                                "cagr": results["cagr"],
                                "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                                "max_drawdown": metrics.get("max_drawdown", 0),
                                "total_trades": metrics.get("total_trades", 0),
                                "win_rate": metrics.get("win_rate", 0),
                                "tested_period": f"{start_year}-{end_year}",
                            }

                            #  Prepare full results for instant restore
                            # Remove charts from full_results (too large, we'll store separately)
                            full_results_copy = results.copy()
                            charts_data = full_results_copy.pop("charts", {})

                            #  Convert ALL numpy arrays to lists (recursively)
                            full_results_json = make_json_serializable(
                                full_results_copy
                            )
                            trades_json = make_json_serializable(trades)

                            # Convert charts to JSON-serializable format
                            # (Plotly charts are already JSON-serializable)
                            charts_json = {
                                key: fig.to_json() if fig is not None else None
                                for key, fig in charts_data.items()
                            }

                            # Save strategy with FULL results
                            strategy_id = storage.save_strategy(
                                name=strategy_name,
                                description=strategy_description,
                                parameters=strategy_params,
                                shared=share_strategy,
                                backtest_results=backtest_summary,
                                universe=universe_name,
                                full_results=full_results_json,
                                trades_data=trades_json,
                                charts_data=charts_json,
                                user_id=st.session_state.get(
                                    "username", "default_user"
                                ),
                            )

                            st.success(
                                f"✅ Strategy '{strategy_name}' saved successfully!"
                            )
                            st.info("🔍 Go to Screening page to use this strategy")

                            # ✅ Clear modal flag
                            st.session_state["show_save_modal"] = False

                            # ✅ Force reload to show new strategy in dropdown
                            import time

                            time.sleep(1.5)  # Let user see success message
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Failed to save strategy: {str(e)}")
        # ====================================================================
        # DOWNLOAD OPTIONS
        # ====================================================================
        st.subheader("💾 Download Results")

        col1, col2, col3 = st.columns(3)

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
                    "use_mos": use_mos,
                    "use_pbt": use_pbt,
                    "use_tencap": use_tencap,
                    "cagr_method": "Auto (5-year historical)",
                    "rebalance_days": rebalance_days,
                    "max_positions": max_positions,
                    "sell_mos_threshold": sell_mos_threshold,
                    "sell_moat_threshold": sell_moat_threshold,
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

        # PDF Report Download
        with col3:
            if st.button("📄 Generate PDF Report", use_container_width=True):
                with st.spinner("Generating PDF report..."):
                    try:
                        from backend.backtesting.analytics.pdf_export import (
                            BacktestPDFExporter,
                        )

                        # Prepare parameters
                        params = {
                            "mos_threshold": mos_threshold,
                            "moat_threshold": moat_threshold,
                            "max_positions": max_positions,
                            "rebalance_days": rebalance_days,
                            "sell_mos_threshold": sell_mos_threshold,
                            "sell_moat_threshold": sell_moat_threshold,
                        }

                        # Generate PDF
                        pdf_bytes = BacktestPDFExporter.generate_report(
                            results=results,
                            charts=charts,
                            universe_name=results.get("universe_display", "Unknown"),
                            parameters=params,
                        )

                        # Download button
                        st.download_button(
                            label="💾 Download PDF Report",
                            data=pdf_bytes,
                            file_name=f"valuekit_report_{date.today()}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )

                        st.success("✅ PDF Report generated!")
                        st.info("ℹ️ Charts available in PowerPoint export")

                    except ImportError as e:
                        st.error(
                            "⚠️ PDF generation requires ReportLab. "
                            "Install with: `pip install reportlab`"
                        )
                    except Exception as e:
                        st.error(f"❌ Failed to generate PDF: {str(e)}")
                        with st.expander("🔍 Error Details"):
                            import traceback

                            st.code(traceback.format_exc())

        # ✅ NEW: PowerPoint Report (Second Row)
        st.divider()

        col1, col2, col3 = st.columns(3)

        with col2:  # Center column
            if st.button(
                "📊 Generate PowerPoint Report",
                use_container_width=True,
                type="primary",
            ):
                with st.spinner("Generating PowerPoint with charts..."):
                    try:
                        from backend.backtesting.analytics.pptx_export import (
                            BacktestPPTXExporter,
                        )

                        # Prepare parameters
                        params = {
                            "mos_threshold": mos_threshold,
                            "moat_threshold": moat_threshold,
                            "max_positions": max_positions,
                            "rebalance_days": rebalance_days,
                            "sell_mos_threshold": sell_mos_threshold,
                            "sell_moat_threshold": sell_moat_threshold,
                        }

                        # Generate PowerPoint
                        pptx_bytes = BacktestPPTXExporter.generate_report(
                            results=results,
                            charts=charts,
                            universe_name=results.get("universe_display", "Unknown"),
                            parameters=params,
                        )

                        # Download button
                        st.download_button(
                            label="💾 Download PowerPoint",
                            data=pptx_bytes,
                            file_name=f"valuekit_presentation_{date.today()}.pptx",
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            use_container_width=True,
                        )

                        st.success("✅ PowerPoint generated with charts!")

                    except ImportError as e:
                        st.error(
                            "⚠️ PowerPoint requires python-pptx. "
                            "Install with: `pip install python-pptx`"
                        )
                    except Exception as e:
                        st.error(f"❌ Failed to generate PowerPoint: {str(e)}")
                        with st.expander("🔍 Error Details"):
                            import traceback

                            st.code(traceback.format_exc())

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
            2. Choose valuation methods (MOS/PBT/TEN CAP)
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
