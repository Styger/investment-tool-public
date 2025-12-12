import streamlit as st
from ..config import get_text, save_persistence_data
import backend.logic.mos as mos_logic
import pandas as pd


def show_mos_analysis():
    """Margin of Safety Analysis Interface with multi-year support"""
    st.header(f"🛡️ {get_text('mos_title')}")
    st.write(get_text("mos_description"))

    persist_data = st.session_state.persist.get("MOS", {})

    # Initialisiere global_ticker falls nicht vorhanden - lade aus Persistence
    if "global_ticker" not in st.session_state:
        st.session_state.global_ticker = st.session_state.persist.get(
            "global_ticker", "MSFT"
        )

    # Checkbox für individuellen Ticker
    use_individual_ticker = st.checkbox(
        get_text("use_individual_ticker", "Use individual ticker"),
        value=persist_data.get("use_individual_ticker", False),
        key="mos_use_individual",
    )

    # ============ LAYOUT: 2 SPALTEN (kein Show Details mehr) ============
    col1, col2 = st.columns(2)

    with col1:
        if use_individual_ticker:
            # Individueller Ticker für dieses Modul
            ticker = st.text_input(
                get_text("ticker_symbol"),
                value=persist_data.get("ticker", ""),
                key="mos_ticker",
            ).upper()
        else:
            # Globaler Ticker - editierbar und synchronisiert
            ticker = st.text_input(
                get_text("ticker_symbol") + " 🌍",
                value=st.session_state.global_ticker,
                key="mos_ticker_global",
                help=get_text(
                    "global_ticker_help", "This ticker will be used across all modules"
                ),
            ).upper()
            # Update global ticker wenn geändert
            if ticker != st.session_state.global_ticker:
                st.session_state.global_ticker = ticker
                # Speichere globalen Ticker in Persistence
                st.session_state.persist["global_ticker"] = ticker
                save_persistence_data()

    with col2:
        multi_year = st.checkbox(
            get_text("multi_year_checkbox", "Multi Year"),
            value=persist_data.get("multi_year", False),
            key="mos_multi",
        )

    # ============ YEAR INPUT - CONDITIONAL ============
    if multi_year:
        col1, col2, col3 = st.columns(3)
        with col1:
            start_year = st.number_input(
                get_text("start_year", "Start Year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("start_year", 2020)),
                key="mos_start",
            )
        with col2:
            end_year = st.number_input(
                get_text("end_year", "End Year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("end_year", 2024)),
                key="mos_end",
            )
        with col3:
            growth_rate = st.number_input(
                get_text("growth_rate", "Growth Rate (%)"),
                min_value=0.0,
                max_value=100.0,
                value=float(persist_data.get("growth_rate", 15.0)),
                step=0.1,
                key="mos_growth",
            )
        years = list(range(start_year, end_year + 1))
    else:
        col1, col2 = st.columns(2)
        with col1:
            single_year = st.number_input(
                get_text("year", "Year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("single_year", 2024)),
                key="mos_single",
            )
        with col2:
            growth_rate = st.number_input(
                get_text("growth_rate", "Growth Rate (%)"),
                min_value=0.0,
                max_value=100.0,
                value=float(persist_data.get("growth_rate", 15.0)),
                step=0.1,
                key="mos_growth",
            )
        years = [single_year]

    # ============ INFO BOX: FIXED MOS 50% ============
    st.info("💡 Margin of Safety is fixed at 50%")

    if st.button(get_text("run_mos_analysis", "Run MOS Analysis"), key="mos_run"):
        if not ticker:
            st.error(get_text("please_enter_ticker", "Please enter a ticker symbol"))
        elif multi_year and start_year >= end_year:
            st.error(
                get_text("start_year_before_end", "Start year must be before end year")
            )
        else:
            with st.spinner(
                get_text("calculating_mos", "Calculating MOS for {0}...").format(ticker)
            ):
                try:
                    # Fixed margin of safety at 50%
                    margin_of_safety = 0.50

                    # Save to persistence (ohne show_details)
                    persist_update = {
                        "ticker": ticker if use_individual_ticker else "",
                        "use_individual_ticker": use_individual_ticker,
                        "multi_year": multi_year,
                        "growth_rate": str(growth_rate),
                    }
                    if multi_year:
                        persist_update.update(
                            {"start_year": str(start_year), "end_year": str(end_year)}
                        )
                    else:
                        persist_update["single_year"] = str(single_year)

                    st.session_state.persist.setdefault("MOS", {}).update(
                        persist_update
                    )
                    save_persistence_data()

                    # Calculate for all years
                    results = []
                    for year in years:
                        result = mos_logic.calculate_mos_value_from_ticker(
                            ticker,
                            year,
                            growth_rate / 100,
                            margin_of_safety=margin_of_safety,
                        )
                        if result:
                            results.append(result)

                    if results:
                        st.success(
                            get_text(
                                "mos_analysis_completed",
                                "MOS analysis completed for {0}",
                            ).format(ticker)
                        )

                        # Get latest year
                        latest_year = max(years)

                        # ============ IMMER TABELLE MIT EPS ============
                        table_data = []
                        for r in results:
                            row = {
                                get_text("year", "Year"): r.get("Year"),
                                get_text("eps", "EPS"): f"${r.get('EPS_now', 0):.2f}",
                                get_text(
                                    "mos_fair_value_today", "Fair Value"
                                ): f"${r.get('Fair Value Today', 0):,.2f}",
                                get_text(
                                    "mos_buy_price", "MOS Price (50%)"
                                ): f"${r.get('MOS Price', 0):,.2f}",
                            }

                            # Add current price & valuation only for latest year
                            if r.get("Year") == latest_year:
                                row[
                                    get_text("current_stock_price", "Current Price")
                                ] = f"${r.get('Current Stock Price', 0):,.2f}"
                                row[get_text("valuation", "Valuation")] = r.get(
                                    "Price vs Fair Value", "N/A"
                                )

                            table_data.append(row)

                        df = pd.DataFrame(table_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)

                        # Info für Multi-Year
                        if multi_year:
                            st.info(
                                get_text(
                                    "current_price_comparison_info",
                                    "Current price comparison shown for year {0}",
                                ).format(latest_year)
                            )

                        # Investment Recommendation für latest year
                        latest = results[-1]
                        recommendation = latest.get("Investment Recommendation", "N/A")

                        st.markdown("### Investment Recommendation")
                        if "Strong Buy" in recommendation:
                            st.success(f"🚀 {recommendation}")
                        elif "Buy" in recommendation:
                            st.success(f"✅ {recommendation}")
                        elif "Hold" in recommendation:
                            st.warning(f"⚖️ {recommendation}")
                        else:
                            st.error(f"❌ {recommendation}")

                    else:
                        st.warning(get_text("no_valid_data", "No valid data available"))

                except Exception as e:
                    st.error(
                        get_text(
                            "mos_analysis_failed", "MOS analysis failed: {0}"
                        ).format(str(e))
                    )
