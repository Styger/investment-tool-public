import streamlit as st
from ..config import get_text, save_persistence_data
import backend.logic.dcf_fmp as dcf_fmp_logic
import backend.logic.dcf_unlevered as dcf_unlevered_logic
import backend.logic.dcf_levered as dcf_levered_logic


def show_dcf_analysis():
    """Enhanced DCF Analysis Interface with three modes and global ticker support"""
    st.header(f"💸 {get_text('dcf.title')}")
    st.write(get_text("dcf.description"))

    # Initialize global_ticker if not present - load from persistence
    if "global_ticker" not in st.session_state:
        st.session_state.global_ticker = st.session_state.persist.get(
            "global_ticker", "MSFT"
        )

    # DCF Mode selection
    dcf_mode = st.selectbox(
        get_text("dcf.method_label"),
        ["fmp (FMP DCF)", "Unlevered (FCFF)", "Levered (FCFE)"],
        key="dcf_mode",
    )

    persist_key = f"DCF_{dcf_mode.split()[0].upper()}"
    persist_data = st.session_state.persist.get(persist_key, {})

    # Checkbox for individual ticker
    use_individual_ticker = st.checkbox(
        get_text("common.use_individual_ticker"),
        value=persist_data.get("use_individual_ticker", False),
        key=f"dcf_{dcf_mode}_use_individual",
    )

    # Common ticker input
    if use_individual_ticker:
        # Individual ticker for this module
        ticker = st.text_input(
            get_text("common.ticker_symbol"),
            value=persist_data.get("ticker", ""),
            key="dcf_ticker",
        ).upper()
    else:
        # Global ticker - editable and synchronized
        ticker = st.text_input(
            get_text("common.ticker_symbol") + " 🌍",
            value=st.session_state.global_ticker,
            key="dcf_ticker_global",
            help=get_text("common.global_ticker_help"),
        ).upper()
        # Update global ticker when changed
        if ticker != st.session_state.global_ticker:
            st.session_state.global_ticker = ticker

    if dcf_mode == "fmp (FMP DCF)":
        show_dcf_fmp_mode(ticker, persist_data, persist_key, use_individual_ticker)
    elif dcf_mode == "Unlevered (FCFF)":
        show_dcf_unlevered_mode(
            ticker, persist_data, persist_key, use_individual_ticker
        )
    elif dcf_mode == "Levered (FCFE)":
        show_dcf_levered_mode(ticker, persist_data, persist_key, use_individual_ticker)


def show_dcf_fmp_mode(ticker, persist_data, persist_key, use_individual_ticker):
    """DCF fmp mode - uses FMP's DCF with integrated MOS"""
    st.subheader(f"📊 {get_text('dcf.fmp_subtitle')}")
    st.write(get_text("dcf.fmp_description"))

    # Parameter input in single row
    mos_percent = (
        st.number_input(
            get_text("dcf.margin_of_safety"),
            min_value=0.0,
            max_value=75.0,
            value=float(persist_data.get("mos_percent", 25.0)),
            step=5.0,
            key="dcf_fmp_mos",
        )
        / 100
    )

    if st.button(get_text("dcf.get_analysis"), key="dcf_fmp_run"):
        if not ticker:
            st.error(get_text("common.please_enter_ticker"))
        else:
            with st.spinner(get_text("dcf.fetching_data").format(ticker)):
                try:
                    # Save to persistence
                    persist_data_update = {
                        "ticker": ticker if use_individual_ticker else "",
                        "use_individual_ticker": use_individual_ticker,
                        "mos_percent": str(mos_percent * 100),
                    }
                    st.session_state.persist.setdefault(persist_key, {}).update(
                        persist_data_update
                    )
                    save_persistence_data()

                    # Use the enhanced backend function
                    data = dcf_fmp_logic.get_dcf_fmp(ticker, mos_percent)

                    st.success(get_text("dcf.analysis_completed").format(ticker))

                    # Main metrics in 4 clean columns
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        if data.get("dcf"):
                            st.metric(
                                get_text("dcf.fair_value"),
                                f"${data['dcf']:,.2f}",
                            )

                    with col2:
                        if data.get("buy_price"):
                            st.metric(
                                get_text("dcf.buy_price_mos").format(
                                    int(mos_percent * 100)
                                ),
                                f"${data['buy_price']:,.2f}",
                            )

                    with col3:
                        if data.get("stock_price"):
                            st.metric(
                                get_text("common.current_stock_price"),
                                f"${data['stock_price']:,.2f}",
                            )

                    with col4:
                        # Price comparison
                        if data.get("price_vs_fair"):
                            comparison = data["price_vs_fair"]
                            if "Undervalued" in comparison:
                                st.success(f"📈 {comparison}")
                            elif "Overvalued" in comparison:
                                st.warning(f"📉 {comparison}")
                            else:
                                st.info(f"⚖️ {comparison}")

                        # Investment Recommendation
                        if data.get("investment_recommendation"):
                            recommendation = data["investment_recommendation"]
                            if "Strong Buy" in recommendation:
                                st.success(f"🚀 {recommendation}")
                            elif "Buy" in recommendation:
                                st.success(f"✅ {recommendation}")
                            elif "Hold" in recommendation:
                                st.warning(f"⚖️ {recommendation}")
                            else:
                                st.error(f"❌ {recommendation}")

                    # Info box
                    st.info(
                        get_text("dcf.fmp_calculation_info").format(
                            int(mos_percent * 100)
                        )
                    )

                    # Data source info
                    if data.get("as_of"):
                        st.caption(get_text("dcf.data_as_of").format(data["as_of"]))

                except Exception as e:
                    st.error(get_text("dcf.analysis_failed").format(str(e)))


def show_dcf_unlevered_mode(ticker, persist_data, persist_key, use_individual_ticker):
    """DCF Unlevered mode - FCFF methodology with integrated MOS"""
    st.subheader(f"🏭 {get_text('dcf.unlevered_subtitle')}")
    st.write(get_text("dcf.unlevered_description"))

    # Main parameters in 4 columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        forecast_years = st.number_input(
            get_text("dcf.forecast_years"),
            min_value=3,
            max_value=15,
            value=int(persist_data.get("forecast_years", 5)),
            key="unlevered_years",
        )

    with col2:
        fcff_growth = (
            st.number_input(
                get_text("dcf.fcff_growth"),
                min_value=0.0,
                max_value=50.0,
                value=float(persist_data.get("fcff_growth", 8.0)),
                step=0.5,
                key="unlevered_growth",
            )
            / 100
        )

    with col3:
        wacc = (
            st.number_input(
                get_text("dcf.wacc"),
                min_value=1.0,
                max_value=25.0,
                value=float(persist_data.get("wacc", 10.0)),
                step=0.5,
                key="unlevered_wacc",
            )
            / 100
        )

    with col4:
        mos_percent = (
            st.number_input(
                get_text("dcf.margin_of_safety"),
                min_value=0.0,
                max_value=75.0,
                value=float(persist_data.get("mos_percent", 25.0)),
                step=5.0,
                key="unlevered_mos",
            )
            / 100
        )

    # Advanced parameters in expander
    with st.expander(get_text("dcf.advanced_parameters")):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            perp_growth = (
                st.number_input(
                    get_text("dcf.terminal_growth"),
                    min_value=0.0,
                    max_value=10.0,
                    value=float(persist_data.get("perp_growth", 3.0)),
                    step=0.5,
                    key="unlevered_perp",
                )
                / 100
            )

        with col2:
            tax_rate = (
                st.number_input(
                    get_text("dcf.tax_rate_auto"),
                    min_value=0.0,
                    max_value=50.0,
                    value=float(persist_data.get("tax_rate", 0.0)),
                    step=1.0,
                    key="unlevered_tax",
                )
                / 100
            )

        with col3:
            base_year = st.number_input(
                get_text("dcf.base_year_optional"),
                min_value=2010,
                max_value=2030,
                value=int(persist_data.get("base_year", 2024)),
                key="unlevered_base_year",
            )

        with col4:
            use_base_year = st.checkbox(
                get_text("dcf.use_specific_base_year"), key="unlevered_use_base"
            )

    if st.button(get_text("dcf.run_unlevered"), key="dcf_unlevered_run"):
        if not ticker:
            st.error(get_text("common.please_enter_ticker"))
        else:
            with st.spinner(get_text("dcf.calculating_unlevered").format(ticker)):
                try:
                    # Save to persistence
                    persist_data_update = {
                        "ticker": ticker if use_individual_ticker else "",
                        "use_individual_ticker": use_individual_ticker,
                        "forecast_years": str(forecast_years),
                        "fcff_growth": str(fcff_growth * 100),
                        "wacc": str(wacc * 100),
                        "perp_growth": str(perp_growth * 100),
                        "base_year": str(base_year),
                        "tax_rate": str(tax_rate * 100),
                        "mos_percent": str(mos_percent * 100),
                    }
                    st.session_state.persist.setdefault(persist_key, {}).update(
                        persist_data_update
                    )
                    save_persistence_data()

                    # Use the enhanced backend function
                    result = dcf_unlevered_logic.dcf_unlevered(
                        ticker=ticker,
                        forecast_years=forecast_years,
                        fcff_growth=fcff_growth,
                        perp_growth=perp_growth,
                        wacc=wacc,
                        tax_rate=tax_rate if tax_rate > 0 else None,
                        mid_year=True,
                        base_year=base_year if use_base_year else None,
                        mos_percent=mos_percent,
                    )

                    st.success(get_text("dcf.unlevered_completed").format(ticker))

                    # Main metrics in 4 clean columns
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        if result.get("fair_value_per_share"):
                            st.metric(
                                get_text("dcf.fair_value_per_share"),
                                f"${result['fair_value_per_share']:,.2f}",
                            )

                    with col2:
                        if result.get("buy_price_per_share"):
                            st.metric(
                                get_text("dcf.buy_price_mos").format(
                                    int(mos_percent * 100)
                                ),
                                f"${result['buy_price_per_share']:,.2f}",
                            )

                    with col3:
                        if result.get("current_stock_price"):
                            st.metric(
                                get_text("common.current_stock_price"),
                                f"${result['current_stock_price']:,.2f}",
                            )
                        st.metric(
                            get_text("dcf.enterprise_value"),
                            f"${result.get('enterprise_value', 0):,.0f}",
                        )

                    with col4:
                        # Price comparison
                        if result.get("price_vs_fair"):
                            comparison = result["price_vs_fair"]
                            if "Undervalued" in comparison:
                                st.success(f"📈 {comparison}")
                            elif "Overvalued" in comparison:
                                st.warning(f"📉 {comparison}")
                            else:
                                st.info(f"⚖️ {comparison}")

                        # Investment Recommendation
                        if result.get("investment_recommendation"):
                            recommendation = result["investment_recommendation"]
                            if "Strong Buy" in recommendation:
                                st.success(f"🚀 {recommendation}")
                            elif "Buy" in recommendation:
                                st.success(f"✅ {recommendation}")
                            elif "Hold" in recommendation:
                                st.warning(f"⚖️ {recommendation}")
                            else:
                                st.error(f"❌ {recommendation}")

                    # Info box
                    st.info(
                        get_text("dcf.fcff_calculation_info").format(
                            fcff_growth * 100,
                            forecast_years,
                            wacc * 100,
                            perp_growth * 100,
                        )
                    )

                    # Detailed breakdown in expandable section
                    with st.expander(f"📊 {get_text('dcf.detailed_calculations')}"):
                        detail_col1, detail_col2 = st.columns(2)

                        with detail_col1:
                            st.metric(
                                get_text("dcf.base_fcff"),
                                f"${result.get('fcff0', 0):,.0f}",
                            )
                            st.metric(
                                get_text("dcf.pv_explicit_fcff"),
                                f"${result.get('pv_explicit', 0):,.0f}",
                            )
                            st.metric(
                                get_text("dcf.wacc_used"),
                                f"{result.get('wacc', 0) * 100:.1f}%",
                            )

                        with detail_col2:
                            if result.get("pv_terminal"):
                                st.metric(
                                    get_text("dcf.pv_terminal_value"),
                                    f"${result['pv_terminal']:,.0f}",
                                )
                            st.metric(
                                get_text("dcf.net_debt"),
                                f"${result.get('net_debt', 0):,.0f}",
                            )
                            st.metric(
                                get_text("dcf.tax_rate_used"),
                                f"{result.get('tax_rate_used', 0) * 100:.1f}%",
                            )

                except Exception as e:
                    st.error(get_text("dcf.unlevered_failed").format(str(e)))


def show_dcf_levered_mode(ticker, persist_data, persist_key, use_individual_ticker):
    """DCF Levered mode - FCFE methodology with integrated MOS"""
    st.subheader(f"🏦 {get_text('dcf.levered_subtitle')}")
    st.write(get_text("dcf.levered_description"))

    # Main parameters in 4 columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        forecast_years = st.number_input(
            get_text("dcf.forecast_years"),
            min_value=3,
            max_value=15,
            value=int(persist_data.get("forecast_years", 5)),
            key="levered_years",
        )

    with col2:
        fcfe_growth = (
            st.number_input(
                get_text("dcf.fcfe_growth"),
                min_value=0.0,
                max_value=50.0,
                value=float(persist_data.get("fcfe_growth", 8.0)),
                step=0.5,
                key="levered_growth",
            )
            / 100
        )

    with col3:
        cost_of_equity = (
            st.number_input(
                get_text("dcf.cost_of_equity"),
                min_value=1.0,
                max_value=25.0,
                value=float(persist_data.get("cost_of_equity", 11.0)),
                step=0.5,
                key="levered_ke",
            )
            / 100
        )

    with col4:
        mos_percent = (
            st.number_input(
                get_text("dcf.margin_of_safety"),
                min_value=0.0,
                max_value=75.0,
                value=float(persist_data.get("mos_percent", 25.0)),
                step=5.0,
                key="levered_mos",
            )
            / 100
        )

    # Advanced parameters in expander
    with st.expander(get_text("dcf.advanced_parameters")):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            perp_growth = (
                st.number_input(
                    get_text("dcf.terminal_growth"),
                    min_value=0.0,
                    max_value=10.0,
                    value=float(persist_data.get("perp_growth", 3.0)),
                    step=0.5,
                    key="levered_perp",
                )
                / 100
            )

        with col2:
            base_year = st.number_input(
                get_text("dcf.base_year_optional"),
                min_value=2010,
                max_value=2030,
                value=int(persist_data.get("base_year", 2024)),
                key="levered_base_year",
            )

        with col3:
            use_base_year = st.checkbox(
                get_text("dcf.use_specific_base_year"), key="levered_use_base"
            )

        with col4:
            pass  # Empty column for alignment

    if st.button(get_text("dcf.run_levered"), key="dcf_levered_run"):
        if not ticker:
            st.error(get_text("common.please_enter_ticker"))
        else:
            with st.spinner(get_text("dcf.calculating_levered").format(ticker)):
                try:
                    # Save to persistence
                    persist_data_update = {
                        "ticker": ticker if use_individual_ticker else "",
                        "use_individual_ticker": use_individual_ticker,
                        "forecast_years": str(forecast_years),
                        "fcfe_growth": str(fcfe_growth * 100),
                        "cost_of_equity": str(cost_of_equity * 100),
                        "perp_growth": str(perp_growth * 100),
                        "base_year": str(base_year),
                        "mos_percent": str(mos_percent * 100),
                    }
                    st.session_state.persist.setdefault(persist_key, {}).update(
                        persist_data_update
                    )
                    save_persistence_data()

                    # Use the enhanced backend function
                    result = dcf_levered_logic.dcf_levered(
                        ticker=ticker,
                        forecast_years=forecast_years,
                        fcfe_growth=fcfe_growth,
                        perp_growth=perp_growth,
                        cost_of_equity=cost_of_equity,
                        mid_year=True,
                        base_year=base_year if use_base_year else None,
                        mos_percent=mos_percent,
                    )

                    st.success(get_text("dcf.levered_completed").format(ticker))

                    # Main metrics in 4 clean columns
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        if result.get("fair_value_per_share"):
                            st.metric(
                                get_text("dcf.fair_value_per_share"),
                                f"${result['fair_value_per_share']:,.2f}",
                            )

                    with col2:
                        if result.get("buy_price_per_share"):
                            st.metric(
                                get_text("dcf.buy_price_mos").format(
                                    int(mos_percent * 100)
                                ),
                                f"${result['buy_price_per_share']:,.2f}",
                            )

                    with col3:
                        if result.get("current_stock_price"):
                            st.metric(
                                get_text("common.current_stock_price"),
                                f"${result['current_stock_price']:,.2f}",
                            )
                        st.metric(
                            get_text("dcf.equity_value"),
                            f"${result.get('equity_value', 0):,.0f}",
                        )

                    with col4:
                        # Price comparison
                        if result.get("price_vs_fair"):
                            comparison = result["price_vs_fair"]
                            if "Undervalued" in comparison:
                                st.success(f"📈 {comparison}")
                            elif "Overvalued" in comparison:
                                st.warning(f"📉 {comparison}")
                            else:
                                st.info(f"⚖️ {comparison}")

                        # Investment Recommendation
                        if result.get("investment_recommendation"):
                            recommendation = result["investment_recommendation"]
                            if "Strong Buy" in recommendation:
                                st.success(f"🚀 {recommendation}")
                            elif "Buy" in recommendation:
                                st.success(f"✅ {recommendation}")
                            elif "Hold" in recommendation:
                                st.warning(f"⚖️ {recommendation}")
                            else:
                                st.error(f"❌ {recommendation}")

                    # Info box
                    st.info(
                        get_text("dcf.fcfe_calculation_info").format(
                            fcfe_growth * 100,
                            forecast_years,
                            cost_of_equity * 100,
                            perp_growth * 100,
                        )
                    )

                    # Detailed breakdown in expandable section
                    with st.expander(f"📊 {get_text('dcf.detailed_calculations')}"):
                        detail_col1, detail_col2 = st.columns(2)

                        with detail_col1:
                            st.metric(
                                get_text("dcf.base_fcfe"),
                                f"${result.get('fcfe0', 0):,.0f}",
                            )
                            st.metric(
                                get_text("dcf.operating_cash_flow"),
                                f"${result.get('cfo', 0):,.0f}",
                            )
                            st.metric(
                                get_text("dcf.capex"),
                                f"${result.get('capex', 0):,.0f}",
                            )

                        with detail_col2:
                            st.metric(
                                get_text("dcf.pv_explicit_fcfe"),
                                f"${result.get('pv_explicit', 0):,.0f}",
                            )
                            if result.get("pv_terminal"):
                                st.metric(
                                    get_text("dcf.pv_terminal_value"),
                                    f"${result['pv_terminal']:,.0f}",
                                )
                            st.metric(
                                get_text("dcf.net_borrowing"),
                                f"${result.get('net_borrowing', 0):,.0f}",
                            )

                except Exception as e:
                    st.error(get_text("dcf.levered_failed").format(str(e)))
