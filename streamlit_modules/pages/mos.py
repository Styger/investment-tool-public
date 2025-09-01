import streamlit as st
from ..config import get_text, save_persistence_data
import logic.mos as mos_logic


def show_mos_analysis():
    """Margin of Safety Analysis Interface"""
    # Ihre bestehende mos_analysis Funktion hier
    st.header(f"🛡️ {get_text('mos_title')}")
    st.write(get_text("mos_description"))

    col1, col2, col3 = st.columns(3)

    persist_data = st.session_state.persist.get("MOS", {})

    with col1:
        ticker = st.text_input(
            get_text("ticker_symbol"),
            value=persist_data.get("ticker", ""),
            key="mos_ticker",
        ).upper()

    with col2:
        year = st.number_input(
            get_text("base_year"),
            min_value=1990,
            max_value=2030,
            value=int(persist_data.get("year", 2024)),
            key="mos_year",
        )

    with col3:
        growth_rate = st.number_input(
            get_text("growth_rate"),
            min_value=0.0,
            max_value=100.0,
            value=float(persist_data.get("growth_rate", 15.0)),
            step=0.1,
            key="mos_growth",
        )

    if st.button(get_text("run_mos_analysis"), key="mos_run"):
        if not ticker:
            st.error(get_text("please_enter_ticker"))
        else:
            with st.spinner(get_text("calculating_mos").format(ticker)):
                try:
                    # Save to persistence
                    persist_data = {
                        "ticker": ticker,
                        "year": str(year),
                        "growth_rate": str(growth_rate),
                    }
                    st.session_state.persist.setdefault("MOS", {}).update(persist_data)
                    save_persistence_data()

                    result = mos_logic.calculate_mos_value_from_ticker(
                        ticker, year, growth_rate / 100
                    )

                    if result:
                        st.success(get_text("mos_analysis_completed").format(ticker))

                        # Display results in a nice format
                        col1, col2 = st.columns(2)

                        with col1:
                            st.metric(
                                get_text("current_eps"),
                                f"${result.get('EPS_now', 0):.2f}",
                            )
                            st.metric(
                                get_text("future_eps_10y"),
                                f"${result.get('EPS_10y', 0):.2f}",
                            )
                            st.metric(
                                get_text("future_value"),
                                f"${result.get('Future Value', 0):,.2f}",
                            )

                        with col2:
                            st.metric(
                                get_text("fair_value_today"),
                                f"${result.get('Fair Value Today', 0):,.2f}",
                            )
                            st.metric(
                                get_text("mos_price_50"),
                                f"${result.get('MOS Price (50%)', 0):,.2f}",
                            )
                            st.metric(
                                get_text("growth_rate_used"),
                                f"{result.get('Growth Rate', 0)}%",
                            )
                    else:
                        st.warning(get_text("no_valid_data"))

                except Exception as e:
                    st.error(get_text("mos_analysis_failed").format(str(e)))
