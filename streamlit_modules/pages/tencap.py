import streamlit as st
import pandas as pd
from ..config import get_text, save_persistence_data, capture_output
import logic.tencap as tencap_logic


def show_tencap_analysis():
    """Ten Cap Analysis Interface"""
    st.header(f"💰 {get_text('ten_cap_title')}")
    st.write(get_text("ten_cap_description"))

    col1, col2, col3 = st.columns(3)

    persist_data = st.session_state.persist.get("TenCap", {})

    with col1:
        ticker = st.text_input(
            get_text("ticker_symbol"),
            value=persist_data.get("ticker", ""),
            key="tencap_ticker",
        ).upper()

    with col2:
        multi_year = st.checkbox(
            get_text("multi_year_checkbox"),
            value=persist_data.get("multi_year", False),
            key="tencap_multi",
        )

    with col3:
        show_details = st.checkbox(
            get_text("details_checkbox"),
            value=persist_data.get("show_details", False),
            key="tencap_details",
        )

    # Year input based on multi-year selection
    if multi_year:
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.number_input(
                get_text("from_year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("start_year", 2020)),
                key="tencap_start",
            )
        with col2:
            end_year = st.number_input(
                get_text("to_year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("end_year", 2024)),
                key="tencap_end",
            )
        years = list(range(start_year, end_year + 1))
    else:
        single_year = st.number_input(
            get_text("year"),
            min_value=1990,
            max_value=2030,
            value=int(persist_data.get("single_year", 2024)),
            key="tencap_single",
        )
        years = [single_year]

    if st.button(get_text("run_tencap_analysis"), key="tencap_run"):
        if not ticker:
            st.error(get_text("please_enter_ticker"))
        elif multi_year and start_year >= end_year:
            st.error(get_text("start_year_before_end"))
        else:
            with st.spinner(get_text("analyzing").format(ticker)):
                try:
                    # Save to persistence
                    persist_update = {
                        "ticker": ticker,
                        "multi_year": multi_year,
                        "show_details": show_details,
                    }
                    if multi_year:
                        persist_update.update(
                            {"start_year": str(start_year), "end_year": str(end_year)}
                        )
                    else:
                        persist_update["single_year"] = str(single_year)

                    st.session_state.persist.setdefault("TenCap", {}).update(
                        persist_update
                    )
                    save_persistence_data()

                    results = []
                    for year in years:
                        try:
                            if show_details:
                                _, output = capture_output(
                                    tencap_logic.print_ten_cap_analysis,
                                    ticker,
                                    year,
                                    st.session_state.language,
                                )
                                if output.strip():
                                    st.text(output)
                            else:
                                price = tencap_logic.calculate_ten_cap_price(
                                    ticker, year
                                )
                                results.append(
                                    {
                                        get_text("year"): year,
                                        get_text("ten_cap_price"): f"${price:,.2f}"
                                        if price
                                        else "N/A",
                                    }
                                )
                        except Exception as e:
                            results.append(
                                {
                                    get_text("year"): year,
                                    get_text(
                                        "ten_cap_price"
                                    ): f"{get_text('error')}: {str(e)}",
                                }
                            )

                    if results and not show_details:
                        df = pd.DataFrame(results)
                        st.dataframe(df, use_container_width=True)

                    st.success(get_text("tencap_analysis_completed").format(ticker))

                except Exception as e:
                    st.error(get_text("tencap_analysis_failed").format(str(e)))
