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
    """Backtesting Analysis Interface with global ticker support"""
    st.header("📊 Backtesting System")
    st.write("Test investment strategies with historical data")

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

    # Checkbox for individual ticker
    use_individual_ticker = st.checkbox(
        get_text("common.use_individual_ticker"),
        value=persist_data.get("use_individual_ticker", False),
        key="backtest_use_individual",
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if use_individual_ticker:
            # Individual ticker for this module
            ticker = st.text_input(
                get_text("common.ticker_symbol"),
                value=persist_data.get("ticker", "AAPL"),
                key="backtest_ticker",
            ).upper()
        else:
            # Global ticker - editable and synchronized
            ticker = st.text_input(
                get_text("common.ticker_symbol") + " 🌍",
                value=st.session_state.global_ticker,
                key="backtest_ticker_global",
                help=get_text("common.global_ticker_help"),
            ).upper()
            # Update global ticker when changed
            if ticker != st.session_state.global_ticker:
                st.session_state.global_ticker = ticker
                st.session_state.persist["global_ticker"] = ticker
                save_persistence_data()

    with col2:
        start_date = st.date_input(
            "Start Date",
            value=datetime.strptime(
                persist_data.get("start_date", "2020-01-01"), "%Y-%m-%d"
            ).date()
            if persist_data.get("start_date")
            else date(2020, 1, 1),
            max_value=date.today(),
            key="backtest_start_date",
        )

    with col3:
        end_date = st.date_input(
            "End Date",
            value=datetime.strptime(
                persist_data.get("end_date", "2023-12-31"), "%Y-%m-%d"
            ).date()
            if persist_data.get("end_date")
            else date(2023, 12, 31),
            max_value=date.today(),
            key="backtest_end_date",
        )

    with col4:
        initial_cash = st.number_input(
            "Initial Capital ($)",
            min_value=1000,
            max_value=1000000,
            value=int(persist_data.get("initial_cash", 10000)),
            step=1000,
            key="backtest_initial_cash",
        )

    # Strategy info
    st.info(
        "**Current Strategy:** Buy & Hold (Milestone 1 PoC)\n\n"
        "**Coming Soon:** ValueKit Strategy with Margin of Safety + Moat Score"
    )

    if st.button("🚀 Run Backtest", key="backtest_run", type="primary"):
        if not ticker:
            st.error(get_text("common.please_enter_ticker"))
        elif start_date >= end_date:
            st.error("Start date must be before end date!")
        else:
            with st.spinner(f"Running backtest for {ticker}..."):
                try:
                    # Save to persistence
                    persist_data = {
                        "ticker": ticker if use_individual_ticker else "",
                        "use_individual_ticker": use_individual_ticker,
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d"),
                        "initial_cash": str(initial_cash),
                    }
                    st.session_state.persist.setdefault("Backtesting", {}).update(
                        persist_data
                    )
                    save_persistence_data()

                    # Import and run backtest
                    from backend.backtesting.backtest_poc import (
                        run_backtest_and_return_results,
                    )

                    results = run_backtest_and_return_results(
                        ticker=ticker,
                        from_date=datetime.combine(start_date, datetime.min.time()),
                        to_date=datetime.combine(end_date, datetime.min.time()),
                        starting_cash=float(initial_cash),
                    )

                    # Store in session state
                    st.session_state["backtest_results"] = results

                    st.success(f"✅ Backtest complete for {ticker}!")

                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
                    import traceback

                    st.code(traceback.format_exc())

    # Display Results
    if "backtest_results" in st.session_state:
        results = st.session_state["backtest_results"]

        st.divider()

        # KPI Metrics
        st.subheader("📈 Performance Summary")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Final Value",
                f"${results['final_value']:,.2f}",
                delta=f"+${results['profit']:,.2f}",
            )

        with col2:
            st.metric("Total Return", f"{results['return_pct']:.2f}%")

        with col3:
            st.metric("CAGR", f"{results['cagr']:.2f}%")

        with col4:
            st.metric("Period", f"{results['years']:.1f} years")

        st.divider()

        # Equity Curve Chart
        st.subheader("📊 Equity Curve")

        from backend.backtesting.visualization import create_equity_curve_chart

        fig = create_equity_curve_chart(
            dates=results["dates"],
            portfolio_values=results["portfolio_values"],
            trades=results.get("trades"),
            title=f"{results['ticker']} - Buy & Hold Strategy ({results['start_date']} to {results['end_date']})",
        )

        # Native Streamlit Plotly integration
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Trade Log
        if "trades" in results and results["trades"]:
            with st.expander("📝 View Trade Details"):
                st.json(results["trades"])

        # Download Options
        st.subheader("💾 Export Results")
        col1, col2 = st.columns(2)

        with col1:
            # Save chart as HTML
            html_file = f"backend/backtesting/results/{results['ticker']}_backtest.html"
            fig.write_html(html_file)

            with open(html_file, "r", encoding="utf-8") as f:
                st.download_button(
                    label="📥 Download Chart (HTML)",
                    data=f.read(),
                    file_name=f"{results['ticker']}_backtest_{date.today()}.html",
                    mime="text/html",
                )

        with col2:
            # Export results as JSON
            import json

            results_json = {
                "ticker": results["ticker"],
                "start_date": str(results["start_date"]),
                "end_date": str(results["end_date"]),
                "starting_value": results["starting_value"],
                "final_value": results["final_value"],
                "profit": results["profit"],
                "return_pct": results["return_pct"],
                "cagr": results["cagr"],
            }

            st.download_button(
                label="📥 Download Results (JSON)",
                data=json.dumps(results_json, indent=2),
                file_name=f"{results['ticker']}_results_{date.today()}.json",
                mime="application/json",
            )

    else:
        # Landing Page (no results yet)
        st.divider()
        st.subheader("📖 How it works")
        st.markdown(
            """
        1. **Select a ticker** (or use global ticker)
        2. **Choose date range** (e.g., 2020-2023)
        3. **Set initial capital** (e.g., $10,000)
        4. **Run backtest** and see results instantly!
        
        **Milestones:**
        - ✅ **M1:** Buy & Hold Strategy (Current)
        - 🔄 **M2:** Historical Data Pipeline (100 stocks)
        - 🔄 **M3:** ValueKit Strategy (MOS + Moat Score)
        - 🔄 **M4:** Performance Metrics (Sharpe, Sortino, Max DD)
        - 🔄 **M5:** Multi-Stock Backtesting
        - 🔄 **M6:** Professional Reports
        """
        )
