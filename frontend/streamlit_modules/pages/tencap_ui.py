import streamlit as st
import pandas as pd
from ..config import get_text, save_persistence_data, capture_output
import backend.logic.tencap as tencap_logic


def show_tencap_analysis():
    """Ten Cap Analysis Interface with global ticker support"""
    st.header(f"🔟 {get_text('tencap.title')}")
    st.write(get_text("tencap.description"))

    persist_data = st.session_state.persist.get("TenCap", {})

    # Initialize global_ticker if not present - load from persistence
    if "global_ticker" not in st.session_state:
        st.session_state.global_ticker = st.session_state.persist.get(
            "global_ticker", "MSFT"
        )

    # Checkbox for individual ticker
    use_individual_ticker = st.checkbox(
        get_text("common.use_individual_ticker"),
        value=persist_data.get("use_individual_ticker", False),
        key="tencap_use_individual",
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if use_individual_ticker:
            # Individual ticker for this module
            ticker = st.text_input(
                get_text("common.ticker_symbol"),
                value=persist_data.get("ticker", ""),
                key="tencap_ticker",
            ).upper()
        else:
            # Global ticker - editable and synchronized
            ticker = st.text_input(
                get_text("common.ticker_symbol") + " 🌍",
                value=st.session_state.global_ticker,
                key="tencap_ticker_global",
                help=get_text("common.global_ticker_help"),
            ).upper()
            # Update global ticker when changed
            if ticker != st.session_state.global_ticker:
                st.session_state.global_ticker = ticker
                # Save global ticker to persistence
                st.session_state.persist["global_ticker"] = ticker
                save_persistence_data()

    with col2:
        multi_year = st.checkbox(
            get_text("common.multi_year_checkbox"),
            value=persist_data.get("multi_year", False),
            key="tencap_multi",
        )

    with col3:
        show_details = st.checkbox(
            get_text("tencap.details_checkbox"),
            value=persist_data.get("show_details", False),
            key="tencap_details",
        )

    # Year input based on multi-year selection
    if multi_year:
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.number_input(
                get_text("common.from_year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("start_year", 2020)),
                key="tencap_start",
            )
        with col2:
            end_year = st.number_input(
                get_text("common.to_year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("end_year", 2024)),
                key="tencap_end",
            )
        years = list(range(start_year, end_year + 1))
    else:
        single_year = st.number_input(
            get_text("common.year"),
            min_value=1990,
            max_value=2030,
            value=int(persist_data.get("single_year", 2024)),
            key="tencap_single",
        )
        years = [single_year]

    if st.button(get_text("tencap.run_analysis"), key="tencap_run"):
        if not ticker:
            st.error(get_text("common.please_enter_ticker"))
        elif multi_year and start_year >= end_year:
            st.error(get_text("common.start_year_before_end"))
        else:
            with st.spinner(get_text("common.analyzing").format(ticker)):
                try:
                    # Save to persistence
                    persist_update = {
                        "ticker": ticker if use_individual_ticker else "",
                        "use_individual_ticker": use_individual_ticker,
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

                    if show_details:
                        # MODIFIED: Load current language from session state
                        current_language_data = st.session_state.get("language", {})

                        # Convert nested structure to flat structure
                        flat_language = {
                            "ten_cap_calc_title": current_language_data.get(
                                "tencap", {}
                            ).get("calc_title", "TEN CAP Analyse für"),
                            "ten_cap_profit_before_tax": current_language_data.get(
                                "tencap", {}
                            ).get("profit_before_tax", "Gewinn vor Steuern:"),
                            "ten_cap_depreciation": current_language_data.get(
                                "tencap", {}
                            ).get("depreciation", "+ Abschreibungen:"),
                            "ten_cap_working_capital": current_language_data.get(
                                "tencap", {}
                            ).get("working_capital", "Δ Working Capital:"),
                            "ten_cap_capex": current_language_data.get(
                                "tencap", {}
                            ).get("capex", "- 50% Maintenance CapEx:"),
                            "ten_cap_owner_earnings": current_language_data.get(
                                "tencap", {}
                            ).get("owner_earnings", "= Owner Earnings:"),
                            "ten_cap_shares": current_language_data.get(
                                "tencap", {}
                            ).get("shares", "Aktien (Mio):"),
                            "ten_cap_eps": current_language_data.get("tencap", {}).get(
                                "eps", "Earnings per Share:"
                            ),
                            "ten_cap_fair_value": current_language_data.get(
                                "tencap", {}
                            ).get("fair_value", "TEN CAP Fair Value:"),
                            "ten_cap_price": current_language_data.get(
                                "tencap", {}
                            ).get("buy_price", "TEN CAP Buy Price:"),
                            "current_stock_price": current_language_data.get(
                                "common", {}
                            ).get("current_stock_price", "Current Stock Price:"),
                            "price_comparison": current_language_data.get(
                                "common", {}
                            ).get("price_comparison", "Price vs. Fair Value:"),
                            "price_vs_fair_value_tencap": current_language_data.get(
                                "tencap", {}
                            ).get("price_vs_fair_value", "Preis vs. Fair Value:"),
                        }

                        # Show details - formatted reports with correct language
                        for year in years:
                            try:
                                _, output = capture_output(
                                    tencap_logic.print_ten_cap_analysis,
                                    ticker,
                                    year,
                                    flat_language,  # MODIFIED: Use current language
                                )
                                if output.strip():
                                    st.code(output, language=None)
                                else:
                                    st.warning(
                                        get_text("tencap.no_details_available").format(
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
                        # Table view (unchanged)
                        results = []
                        latest_year = max(years)
                        current_price_data = None

                        # Get current price from latest year
                        try:
                            latest_result = (
                                tencap_logic.calculate_ten_cap_with_comparison(
                                    ticker, latest_year
                                )
                            )
                            if (
                                latest_result
                                and latest_result.get("current_stock_price") is not None
                            ):
                                current_price_data = {
                                    "price": latest_result["current_stock_price"],
                                    "fair_value": latest_result.get(
                                        "ten_cap_fair_value"
                                    ),
                                    "buy_price": latest_result.get("ten_cap_buy_price"),
                                    "comparison": latest_result.get(
                                        "price_vs_fair_value_tencap", "N/A"
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

                        # Collect all results
                        for year in years:
                            try:
                                result_data = (
                                    tencap_logic.calculate_ten_cap_with_comparison(
                                        ticker, year
                                    )
                                )

                                if result_data:
                                    fair_value = result_data.get("ten_cap_fair_value")
                                    buy_price = result_data.get("ten_cap_buy_price")

                                    row = {
                                        get_text("common.year"): year,
                                        get_text(
                                            "tencap.fair_value"
                                        ): f"${fair_value:,.2f}"
                                        if fair_value
                                        else "N/A",
                                        get_text(
                                            "tencap.buy_price"
                                        ): f"${buy_price:,.2f}" if buy_price else "N/A",
                                    }

                                    # Add current price only for latest year
                                    if year == latest_year and current_price_data:
                                        row[get_text("common.current_stock_price")] = (
                                            f"${current_price_data['price']:,.2f}"
                                        )
                                        row[get_text("tencap.price_vs_fair_value")] = (
                                            current_price_data["comparison"]
                                        )

                                    results.append(row)
                                else:
                                    results.append(
                                        {
                                            get_text("common.year"): year,
                                            get_text("tencap.fair_value"): "N/A",
                                            get_text("tencap.buy_price"): "N/A",
                                        }
                                    )

                            except Exception as e:
                                results.append(
                                    {
                                        get_text("common.year"): year,
                                        get_text(
                                            "tencap.fair_value"
                                        ): f"{get_text('common.error')}: {str(e)}",
                                        get_text(
                                            "tencap.buy_price"
                                        ): f"{get_text('common.error')}: {str(e)}",
                                    }
                                )

                        if results:
                            # Special display for single year
                            if len(years) == 1 and current_price_data:
                                st.subheader(
                                    get_text("tencap.analysis_for").format(ticker)
                                )

                                # Display metrics in 4 columns
                                col1, col2, col3, col4 = st.columns(4)

                                with col1:
                                    st.metric(
                                        get_text("tencap.fair_value"),
                                        f"${current_price_data['fair_value']:,.2f}",
                                    )

                                with col2:
                                    st.metric(
                                        get_text("tencap.buy_price"),
                                        f"${current_price_data['buy_price']:,.2f}",
                                    )

                                with col3:
                                    st.metric(
                                        get_text("common.current_stock_price"),
                                        f"${current_price_data['price']:,.2f}",
                                    )

                                with col4:
                                    # Valuation based on fair value
                                    valuation = current_price_data["comparison"]
                                    if "Undervalued" in valuation:
                                        st.success(f"📈 {valuation}")
                                    elif "Overvalued" in valuation:
                                        st.warning(f"📉 {valuation}")
                                    else:
                                        st.info(f"⚖️ {valuation}")

                                    # Investment recommendation
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

                                # Central info box
                                st.info(f"💡 {get_text('tencap.calculation_info')}")

                            # Display table for all cases
                            df = pd.DataFrame(results)
                            st.dataframe(df, use_container_width=True, hide_index=True)

                            # Additional info for multi-year
                            if multi_year and current_price_data:
                                st.info(
                                    get_text(
                                        "common.current_price_comparison_info"
                                    ).format(latest_year)
                                )

                    st.success(get_text("tencap.analysis_completed").format(ticker))

                except Exception as e:
                    st.error(get_text("tencap.analysis_failed").format(str(e)))
