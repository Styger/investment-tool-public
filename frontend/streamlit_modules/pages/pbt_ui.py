import streamlit as st
import pandas as pd
from ..config import get_text, save_persistence_data, capture_output
import backend.logic.pbt as pbt_logic


def show_pbt_analysis():
    """Payback Time Analysis Interface with global ticker support and multi-year"""

    st.header(f"⏰ {get_text('pbt.title')}")
    st.write(get_text("pbt.description"))

    persist_data = st.session_state.persist.get("PBT", {})

    if "global_ticker" not in st.session_state:
        st.session_state.global_ticker = st.session_state.persist.get(
            "global_ticker", "MSFT"
        )

    use_individual_ticker = st.checkbox(
        get_text("common.use_individual_ticker"),
        value=persist_data.get("use_individual_ticker", False),
        key="pbt_use_individual",
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if use_individual_ticker:
            ticker = st.text_input(
                get_text("common.ticker_symbol"),
                value=persist_data.get("ticker", ""),
                key="pbt_ticker",
            ).upper()
        else:
            ticker = st.text_input(
                get_text("common.ticker_symbol") + " 🌍",
                value=st.session_state.global_ticker,
                key="pbt_ticker_global",
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
            key="pbt_multi",
        )

    with col3:
        show_details = st.checkbox(
            get_text("pbt.details_checkbox"),
            value=persist_data.get("show_details", False),
            key="pbt_details",
        )

    col1, col2 = st.columns(2)

    with col1:
        if multi_year:
            subcol1, subcol2 = st.columns(2)
            with subcol1:
                start_year = st.number_input(
                    get_text("common.from_year"),
                    min_value=1990,
                    max_value=2030,
                    value=int(persist_data.get("start_year", 2020)),
                    key="pbt_start",
                )
            with subcol2:
                end_year = st.number_input(
                    get_text("common.to_year"),
                    min_value=1990,
                    max_value=2030,
                    value=int(persist_data.get("end_year", 2024)),
                    key="pbt_end",
                )
            years = list(range(start_year, end_year + 1))
        else:
            single_year = st.number_input(
                get_text("common.year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("single_year", 2024)),
                key="pbt_single",
            )
            years = [single_year]

    with col2:
        growth_rate = st.number_input(
            get_text("pbt.growth_rate"),
            min_value=0.0,
            max_value=100.0,
            value=float(persist_data.get("growth_rate", 13.0)),
            step=0.1,
            key="pbt_growth",
        )

    if st.button(get_text("pbt.run_analysis"), key="pbt_run_button"):
        if not ticker:
            st.error(get_text("common.please_enter_ticker"))
        elif multi_year and start_year >= end_year:
            st.error(get_text("common.start_year_before_end"))
        else:
            with st.spinner(get_text("pbt.calculating").format(ticker)):
                try:
                    persist_update = {
                        "ticker": ticker if use_individual_ticker else "",
                        "use_individual_ticker": use_individual_ticker,
                        "multi_year": multi_year,
                        "show_details": show_details,
                        "growth_rate": str(growth_rate),
                    }
                    if multi_year:
                        persist_update.update(
                            {"start_year": str(start_year), "end_year": str(end_year)}
                        )
                    else:
                        persist_update["single_year"] = str(single_year)

                    st.session_state.persist.setdefault("PBT", {}).update(
                        persist_update
                    )
                    save_persistence_data()

                    if show_details:
                        current_language_data = st.session_state.get("language", {})

                        for year in years:
                            try:
                                _, output = capture_output(
                                    pbt_logic.print_pbt_analysis,
                                    ticker,
                                    year,
                                    growth_rate / 100,
                                    current_language_data,
                                )
                                if output.strip():
                                    st.code(output, language=None)
                                else:
                                    st.warning(
                                        get_text("pbt.no_details_available").format(
                                            year
                                        )
                                    )
                            except Exception as e:
                                st.error(
                                    get_text("common.error_for_year").format(
                                        year, str(e)
                                    )
                                )
                    else:
                        results = []
                        latest_year = max(years)
                        current_price_data = None

                        try:
                            latest_result = pbt_logic.calculate_pbt_with_comparison(
                                ticker, latest_year, growth_rate / 100
                            )
                            if (
                                latest_result
                                and latest_result.get("current_stock_price") is not None
                            ):
                                current_price_data = {
                                    "price": latest_result["current_stock_price"],
                                    "buy_price": latest_result.get("buy_price"),
                                    "fair_value": latest_result.get("fair_value"),
                                    "comparison": latest_result.get(
                                        "price_comparison", "N/A"
                                    ),
                                    "recommendation": latest_result.get(
                                        "investment_recommendation", "N/A"
                                    ),
                                }
                        except Exception as e:
                            st.warning(
                                get_text("common.could_not_fetch_current_price").format(
                                    str(e)
                                )
                            )

                        for year in years:
                            try:
                                result_data = pbt_logic.calculate_pbt_with_comparison(
                                    ticker, year, growth_rate / 100
                                )

                                if result_data:
                                    buy_price = result_data.get("buy_price")
                                    fair_value = result_data.get("fair_value")
                                    fcf = result_data.get("fcf_per_share")

                                    row = {
                                        get_text("common.year"): year,
                                        get_text("pbt.fcf_per_share"): f"${fcf:,.2f}"
                                        if fcf
                                        else "N/A",
                                        get_text(
                                            "pbt.buy_price_8y"
                                        ): f"${buy_price:,.2f}" if buy_price else "N/A",
                                        get_text(
                                            "pbt.fair_value_2x"
                                        ): f"${fair_value:,.2f}"
                                        if fair_value
                                        else "N/A",
                                    }

                                    if year == latest_year and current_price_data:
                                        row[get_text("common.current_stock_price")] = (
                                            f"${current_price_data['price']:,.2f}"
                                        )
                                        row[get_text("pbt.price_comparison")] = (
                                            current_price_data["comparison"]
                                        )

                                    results.append(row)
                                else:
                                    results.append(
                                        {
                                            get_text("common.year"): year,
                                            get_text("pbt.fcf_per_share"): "N/A",
                                            get_text("pbt.buy_price_8y"): "N/A",
                                            get_text("pbt.fair_value_2x"): "N/A",
                                        }
                                    )

                            except Exception as e:
                                results.append(
                                    {
                                        get_text("common.year"): year,
                                        get_text(
                                            "pbt.fcf_per_share"
                                        ): f"{get_text('common.error')}: {str(e)}",
                                        get_text(
                                            "pbt.buy_price_8y"
                                        ): f"{get_text('common.error')}: {str(e)}",
                                        get_text(
                                            "pbt.fair_value_2x"
                                        ): f"{get_text('common.error')}: {str(e)}",
                                    }
                                )

                        if results:
                            if len(years) == 1 and current_price_data:
                                st.subheader(
                                    get_text("pbt.analysis_for").format(ticker)
                                )

                                col1, col2, col3, col4 = st.columns(4)

                                with col1:
                                    st.metric(
                                        get_text("pbt.buy_price_8y"),
                                        f"${current_price_data['buy_price']:,.2f}",
                                    )

                                with col2:
                                    st.metric(
                                        get_text("pbt.fair_value_2x"),
                                        f"${current_price_data['fair_value']:,.2f}",
                                    )

                                with col3:
                                    st.metric(
                                        get_text("common.current_stock_price"),
                                        f"${current_price_data['price']:,.2f}",
                                    )

                                with col4:
                                    valuation = current_price_data["comparison"]
                                    if "Below buy price" in valuation:
                                        st.success(f"📈 {valuation}")
                                    elif "Below fair value" in valuation:
                                        st.info(f"✅ {valuation}")
                                    elif "Overvalued" in valuation:
                                        st.warning(f"📉 {valuation}")
                                    else:
                                        st.info(f"⚖️ {valuation}")

                                    recommendation = current_price_data[
                                        "recommendation"
                                    ]
                                    if "Strong Buy" in recommendation:
                                        st.success(f"🚀 {recommendation}")
                                    elif "Buy" in recommendation:
                                        st.success(f"✅ {recommendation}")
                                    elif "Hold" in recommendation:
                                        st.warning(f"⚖️ {recommendation}")
                                    else:
                                        st.error(f"❌ {recommendation}")

                                st.info(get_text("pbt.calculation_info_simple"))

                            df = pd.DataFrame(results)
                            st.dataframe(df, use_container_width=True, hide_index=True)

                            if multi_year and current_price_data:
                                st.info(
                                    get_text(
                                        "common.current_price_comparison_info"
                                    ).format(latest_year)
                                )

                    st.success(get_text("pbt.analysis_completed").format(ticker))

                except Exception as e:
                    st.error(get_text("pbt.analysis_failed").format(str(e)))
