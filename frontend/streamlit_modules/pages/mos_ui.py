import streamlit as st
from ..config import get_text, save_persistence_data
import backend.logic.mos as mos_logic
import pandas as pd


def show_mos_analysis():
    """Margin of Safety Analysis Interface with multi-year support"""
    st.header(f"🛡️ {get_text('mos.title')}")
    st.write(get_text("mos.description"))

    persist_data = st.session_state.persist.get("MOS", {})

    if "global_ticker" not in st.session_state:
        st.session_state.global_ticker = st.session_state.persist.get(
            "global_ticker", "MSFT"
        )

    use_individual_ticker = st.checkbox(
        get_text("common.use_individual_ticker"),
        value=persist_data.get("use_individual_ticker", False),
        key="mos_use_individual",
    )

    col1, col2 = st.columns(2)

    with col1:
        if use_individual_ticker:
            ticker = st.text_input(
                get_text("common.ticker_symbol"),
                value=persist_data.get("ticker", ""),
                key="mos_ticker",
            ).upper()
        else:
            ticker = st.text_input(
                get_text("common.ticker_symbol") + " 🌍",
                value=st.session_state.global_ticker,
                key="mos_ticker_global",
                help=get_text("common.global_ticker_help"),
            ).upper()
            if ticker != st.session_state.global_ticker:
                st.session_state.global_ticker = ticker
                st.session_state.persist["global_ticker"] = ticker
                save_persistence_data()

    with col2:
        multi_year = st.checkbox(
            get_text("common.multi_year_checkbox"),
            value=persist_data.get("multi_year", False),
            key="mos_multi",
        )

    if multi_year:
        col1, col2, col3 = st.columns(3)
        with col1:
            start_year = st.number_input(
                get_text("common.start_year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("start_year", 2020)),
                key="mos_start",
            )
        with col2:
            end_year = st.number_input(
                get_text("common.end_year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("end_year", 2024)),
                key="mos_end",
            )
        with col3:
            growth_rate = st.number_input(
                get_text("mos.growth_rate"),
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
                get_text("common.year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("single_year", 2024)),
                key="mos_single",
            )
        with col2:
            growth_rate = st.number_input(
                get_text("mos.growth_rate"),
                min_value=0.0,
                max_value=100.0,
                value=float(persist_data.get("growth_rate", 15.0)),
                step=0.1,
                key="mos_growth",
            )
        years = [single_year]

    st.info(f"💡 {get_text('mos.mos_fixed_info')}")

    if st.button(get_text("mos.run_analysis"), key="mos_run"):
        if not ticker:
            st.error(get_text("common.please_enter_ticker"))
        elif multi_year and start_year >= end_year:
            st.error(get_text("common.start_year_before_end"))
        else:
            with st.spinner(get_text("mos.calculating").format(ticker)):
                try:
                    margin_of_safety = 0.50

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
                        st.success(get_text("mos.analysis_completed").format(ticker))

                        latest_year = max(years)

                        table_data = []
                        for r in results:
                            row = {
                                get_text("common.year"): r.get("Year"),
                                get_text("mos.eps"): f"${r.get('EPS_now', 0):.2f}",
                                get_text(
                                    "mos.fair_value_today"
                                ): f"${r.get('Fair Value Today', 0):,.2f}",
                                get_text(
                                    "mos.buy_price"
                                ): f"${r.get('MOS Price', 0):,.2f}",
                            }

                            if r.get("Year") == latest_year:
                                row[get_text("common.current_stock_price")] = (
                                    f"${r.get('Current Stock Price', 0):,.2f}"
                                )
                                row[get_text("mos.valuation")] = r.get(
                                    "Price vs Fair Value", "N/A"
                                )

                            table_data.append(row)

                        df = pd.DataFrame(table_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)

                        if multi_year:
                            st.info(
                                get_text("mos.current_price_comparison_info").format(
                                    latest_year
                                )
                            )

                        latest = results[-1]
                        recommendation = latest.get("Investment Recommendation", "N/A")

                        st.markdown(f"### {get_text('mos.investment_recommendation')}")
                        if "Strong Buy" in recommendation:
                            st.success(f"🚀 {recommendation}")
                        elif "Buy" in recommendation:
                            st.success(f"✅ {recommendation}")
                        elif "Hold" in recommendation:
                            st.warning(f"⚖️ {recommendation}")
                        else:
                            st.error(f"❌ {recommendation}")

                    else:
                        st.warning(get_text("common.no_valid_data"))

                except Exception as e:
                    st.error(get_text("mos.analysis_failed").format(str(e)))
