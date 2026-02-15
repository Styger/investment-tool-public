"""
Live Market Screening Page
Screen S&P 500 with saved strategies
"""

import streamlit as st
import pandas as pd
from datetime import date
import time


def show_screening_page():
    """Main screening page with job queue support"""
    # ====================================================================
    # ROUTE TO JOBS PAGE IF REQUESTED
    # ====================================================================
    if st.session_state.get("current_page") == "screening_jobs":
        from frontend.streamlit_modules.pages.screening_jobs_ui import (
            show_screening_jobs_page,
        )

        show_screening_jobs_page()
        return
    # ====================================================================
    # NORMAL SCREENING PAGE (only if NOT on jobs page)
    # ====================================================================
    # Page config
    st.set_page_config(
        page_title="Live Screening - ValueKit",
        page_icon="🔍",
        layout="wide",
    )

    st.title("🔍 Live Market Screening")
    st.markdown("Screen the S&P 500 with your saved strategies")

    # ====================================================================
    # LOAD STRATEGIES
    # ====================================================================
    try:
        from backend.storage.strategy_storage import StrategyStorage

        storage = StrategyStorage()

        # Get actual logged-in user
        current_user = st.session_state.get("username", "default_user")
        strategies = storage.get_strategies(user_id=current_user, include_shared=True)

        if not strategies:
            st.warning(
                "⚠️ **No strategies found!**\n\n"
                "Go to Backtesting page to create and save a strategy first."
            )

            if st.button("📊 Go to Backtesting"):
                st.switch_page("pages/backtesting.py")

            return

    except Exception as e:
        st.error(f"❌ Error loading strategies: {str(e)}")
        st.stop()

    # ====================================================================
    # STRATEGY SELECTION
    # ====================================================================
    st.subheader("📋 Select Strategy")

    # Create strategy options
    strategy_options = {}
    for strategy in strategies:
        # Add shared/private indicator
        shared_icon = "🌍" if strategy.get("shared") else "📌"

        # Add performance if available
        perf = ""
        if strategy.get("backtest_results"):
            results = strategy["backtest_results"]
            perf = f" - CAGR: {results.get('cagr', 0):.1f}%, Win: {results.get('win_rate', 0):.0f}%"

        label = f"{shared_icon} {strategy['name']}{perf}"
        strategy_options[label] = strategy

    col1, col2 = st.columns([3, 1])

    with col1:
        selected_label = st.selectbox(
            "Strategy",
            options=list(strategy_options.keys()),
            help="Select a saved strategy to use for screening",
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        if st.button("🔄 Refresh", help="Reload strategies", use_container_width=True):
            st.rerun()

    selected_strategy = strategy_options[selected_label]

    # Delete strategy functionality
    can_delete = selected_strategy.get("user_id") == current_user

    if st.button(
        "🗑️ Delete This Strategy",
        type="secondary",
        disabled=not can_delete,
        help="Delete this strategy"
        if can_delete
        else "Cannot delete shared strategies",
    ):
        if can_delete:
            st.session_state["confirm_delete_screening"] = selected_strategy
            st.rerun()

    # Confirmation dialog
    if "confirm_delete_screening" in st.session_state:
        strategy_to_delete = st.session_state["confirm_delete_screening"]

        st.divider()
        st.error(f"⚠️ **Confirm Deletion**")
        st.warning(
            f"Delete strategy: **{strategy_to_delete['name']}**?\n\nThis action cannot be undone!"
        )

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("✅ Yes, Delete", type="primary", use_container_width=True):
                try:
                    from backend.storage.strategy_storage import StrategyStorage

                    storage = StrategyStorage()

                    success = storage.delete_strategy(
                        strategy_id=strategy_to_delete["id"],
                        user_id=current_user,
                    )

                    if success:
                        st.success(f"✅ Deleted '{strategy_to_delete['name']}'")
                        del st.session_state["confirm_delete_screening"]
                        if "screening_results" in st.session_state:
                            del st.session_state["screening_results"]

                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete strategy")

                except Exception as e:
                    st.error(f"❌ Error deleting strategy: {str(e)}")

        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                del st.session_state["confirm_delete_screening"]
                st.rerun()

    # Show strategy details
    with st.expander("📋 Strategy Details", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Parameters:**")
            params = selected_strategy["parameters"]
            st.write(f"- MOS Threshold: {params.get('mos_threshold', 0)}%")
            st.write(f"- Moat Threshold: {params.get('moat_threshold', 0)}/50")
            st.write(f"- Sell MOS: {params.get('sell_mos_threshold', 0)}%")
            st.write(f"- Sell Moat: {params.get('sell_moat_threshold', 0)}/50")

            methods = []
            if params.get("use_mos"):
                methods.append("MOS")
            if params.get("use_pbt"):
                methods.append("PBT")
            if params.get("use_tencap"):
                methods.append("TEN CAP")
            st.write(f"- Methods: {', '.join(methods)}")

        with col2:
            if selected_strategy.get("description"):
                st.markdown("**Description:**")
                st.write(selected_strategy["description"])

            if selected_strategy.get("backtest_results"):
                st.markdown("**Backtest Results:**")
                results = selected_strategy["backtest_results"]
                st.write(f"- Return: {results.get('return_pct', 0):.2f}%")
                st.write(f"- CAGR: {results.get('cagr', 0):.2f}%")
                st.write(f"- Sharpe: {results.get('sharpe_ratio', 0):.2f}")
                st.write(f"- Win Rate: {results.get('win_rate', 0):.0f}%")

    st.divider()

    # ====================================================================
    # UNIVERSE SELECTION
    # ====================================================================
    st.subheader("🌍 Select Stock Universe")

    from backend.backtesting.universe.definitions import list_universes

    universes = list_universes()

    # Create options for selectbox
    universe_options = {
        f"{u['name']} ({u['count']} stocks)": u["key"] for u in universes
    }

    selected_universe_label = st.selectbox(
        "Universe",
        options=list(universe_options.keys()),
        index=0,  # Default to first (S&P 500 Full)
        help="Choose which stocks to screen",
    )

    selected_universe_key = universe_options[selected_universe_label]

    # Show universe details
    selected_universe_info = next(
        u for u in universes if u["key"] == selected_universe_key
    )

    st.caption(f"📊 {selected_universe_info['description']}")

    st.divider()

    # ====================================================================
    # SCREENING OPTIONS
    # ====================================================================
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("🔍 Screen Market")

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        # NAVIGATE TO JOBS PAGE
        if st.button(
            "📊 My Jobs", use_container_width=True, help="View screening jobs"
        ):
            st.session_state["current_page"] = "screening_jobs"
            st.rerun()

    # Choose screening mode
    screening_mode = st.radio(
        "Screening Mode",
        options=[
            "⚡ Instant (Wait for Results)",
            "🚀 Background Job (Come Back Later)",
        ],
        index=1,  # Default to background
        help="Instant: Wait 1-2 minutes for results. Background: Submit job and check later.",
    )

    st.info(
        "🎯 **What happens:**\n\n"
        "We'll screen the selected stock universe with your strategy parameters "
        "and show which ones are BUY, HOLD, or SELL right now."
    )

    # ====================================================================
    # INSTANT SCREENING (OLD METHOD)
    # ====================================================================
    if screening_mode == "⚡ Instant (Wait for Results)":
        if st.button("🔍 Screen Now", type="primary", use_container_width=True):
            with st.spinner("Screening market... This may take 1-2 minutes..."):
                try:
                    from backend.screening.screener import Screener

                    # Run screening
                    results_df = Screener.screen_market(
                        strategy_params=selected_strategy["parameters"],
                        universe_key=selected_universe_key,
                    )

                    if results_df.empty:
                        st.error(
                            "❌ No results found. Please try again or check your data connection."
                        )
                    else:
                        # Store results in session state
                        st.session_state["screening_results"] = results_df
                        st.session_state["screening_date"] = date.today()
                        st.session_state["screening_strategy"] = selected_strategy[
                            "name"
                        ]
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Screening failed: {str(e)}")
                    with st.expander("🔍 Error Details"):
                        import traceback

                        st.code(traceback.format_exc())

    # ====================================================================
    # BACKGROUND JOB (NEW METHOD)
    # ====================================================================
    else:  # Background Job
        if st.button(
            "🚀 Submit Screening Job", type="primary", use_container_width=True
        ):
            try:
                from backend.jobs.screening_queue import ScreeningJobQueue

                queue = ScreeningJobQueue()

                # Submit job
                job_id = queue.submit_job(
                    user_id=current_user,
                    strategy_id=selected_strategy["id"],
                    strategy_name=selected_strategy["name"],
                    universe_key=selected_universe_key,
                    universe_name=selected_universe_info["name"],
                    parameters=selected_strategy["parameters"],
                )

                st.success(f"✅ Screening job submitted! Job ID: `{job_id[:8]}...`")

                # NAVIGATE TO JOBS PAGE
                time.sleep(1.5)
                st.session_state["current_page"] = "screening_jobs"
                st.rerun()

            except Exception as e:
                st.error(f"❌ Failed to submit job: {str(e)}")
                with st.expander("🔍 Error Details"):
                    import traceback

                    st.code(traceback.format_exc())

    # ====================================================================
    # DISPLAY RESULTS
    # ====================================================================
    if "screening_results" in st.session_state:
        st.divider()
        st.subheader("📊 Screening Results")

        results_df = st.session_state["screening_results"]
        screening_date = st.session_state.get("screening_date", date.today())
        strategy_name = st.session_state.get("screening_strategy", "Unknown")

        st.caption(
            f"Strategy: {strategy_name} | Screened: {screening_date} | Total: {len(results_df)} stocks"
        )

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        buy_stocks = results_df[results_df["Signal"] == "BUY"]
        hold_stocks = results_df[results_df["Signal"] == "HOLD"]
        sell_stocks = results_df[results_df["Signal"] == "SELL"]

        with col1:
            st.metric("🟢 BUY Signals", len(buy_stocks))

        with col2:
            st.metric("🟡 HOLD", len(hold_stocks))

        with col3:
            st.metric("🔴 SELL Signals", len(sell_stocks))

        with col4:
            avg_mos = results_df["MOS %"].mean()
            st.metric("Avg MOS", f"{avg_mos:.1f}%")

        # Tabs for signals
        tab1, tab2, tab3, tab4 = st.tabs(["🟢 BUY", "🟡 HOLD", "🔴 SELL", "📊 All"])

        with tab1:
            if len(buy_stocks) > 0:
                st.dataframe(
                    buy_stocks.sort_values("MOS %", ascending=False),
                    use_container_width=True,
                    hide_index=True,
                )

                # Download
                csv = buy_stocks.to_csv(index=False)
                st.download_button(
                    "📥 Download BUY signals (CSV)",
                    data=csv,
                    file_name=f"buy_signals_{screening_date}.csv",
                    mime="text/csv",
                )
            else:
                st.info("No BUY signals found")

        with tab2:
            if len(hold_stocks) > 0:
                st.dataframe(
                    hold_stocks.sort_values("MOS %", ascending=False),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No HOLD signals")

        with tab3:
            if len(sell_stocks) > 0:
                st.dataframe(
                    sell_stocks.sort_values("MOS %", ascending=True),
                    use_container_width=True,
                    hide_index=True,
                )

                # Download
                csv = sell_stocks.to_csv(index=False)
                st.download_button(
                    "📥 Download SELL signals (CSV)",
                    data=csv,
                    file_name=f"sell_signals_{screening_date}.csv",
                    mime="text/csv",
                )
            else:
                st.info("No SELL signals")

        with tab4:
            st.dataframe(
                results_df.sort_values("MOS %", ascending=False),
                use_container_width=True,
                hide_index=True,
            )

            # Download all
            csv = results_df.to_csv(index=False)
            st.download_button(
                "📥 Download All Results (CSV)",
                data=csv,
                file_name=f"screening_results_{screening_date}.csv",
                mime="text/csv",
            )
