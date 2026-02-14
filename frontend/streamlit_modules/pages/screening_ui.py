"""
Live Market Screening Page
Screen S&P 500 with saved strategies
"""

import streamlit as st
import pandas as pd
from datetime import date


def show_screening_page():
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
        strategies = storage.get_strategies(user_id="default_user", include_shared=True)

        if not strategies:
            st.warning(
                "⚠️ **No strategies found!**\n\n"
                "Go to Backtesting page to create and save a strategy first."
            )

            if st.button("📊 Go to Backtesting"):
                st.switch_page("pages/backtesting.py")

            st.stop()

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
        # Add owner indicator
        owner = " (You)" if strategy["user_id"] == "default_user" else " (Shared)"

        # Add performance if available
        perf = ""
        if strategy.get("backtest_results"):
            results = strategy["backtest_results"]
            perf = f" - CAGR: {results.get('cagr', 0):.1f}%, Win: {results.get('win_rate', 0):.0f}%"

        label = f"{strategy['name']}{owner}{perf}"
        strategy_options[label] = strategy

    selected_label = st.selectbox(
        "Strategy",
        options=list(strategy_options.keys()),
        help="Select a saved strategy to use for screening",
    )

    selected_strategy = strategy_options[selected_label]

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
    # SCREENING
    # ====================================================================
    st.subheader("🔍 Screen Market")

    st.info(
        "🎯 **What happens:**\n\n"
        "We'll screen 50 S&P 500 stocks with your strategy parameters "
        "and show which ones are BUY, HOLD, or SELL right now."
    )

    if st.button("🔍 Screen S&P 500 Now", type="primary", width="stretch"):
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
                    st.session_state["screening_strategy"] = selected_strategy["name"]
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Screening failed: {str(e)}")
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
