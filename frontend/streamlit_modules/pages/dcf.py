import streamlit as st
from ..config import get_text, save_persistence_data
import backend.logic.dcf_fmp as dcf_fmp_logic
import backend.logic.dcf_unlevered as dcf_unlevered_logic
import backend.logic.dcf_levered as dcf_levered_logic


def show_dcf_analysis():
    """Enhanced DCF Analysis Interface with three modes"""
    st.header(f"💰 {get_text('dcf_fmp_title')}")
    st.write("Comprehensive DCF valuation with multiple methodologies.")

    # DCF Mode selection
    dcf_mode = st.selectbox(
        "DCF Method",
        ["fmp (FMP DCF)", "Unlevered (FCFF)", "Levered (FCFE)"],
        key="dcf_mode",
    )

    persist_key = f"DCF_{dcf_mode.split()[0].upper()}"
    persist_data = st.session_state.persist.get(persist_key, {})

    # Common ticker input
    ticker = st.text_input(
        get_text("ticker_symbol"),
        value=persist_data.get("ticker", ""),
        key="dcf_ticker",
    ).upper()

    if dcf_mode == "fmp (FMP DCF)":
        show_dcf_fmp_mode(ticker, persist_data, persist_key)
    elif dcf_mode == "Unlevered (FCFF)":
        show_dcf_unlevered_mode(ticker, persist_data, persist_key)
    elif dcf_mode == "Levered (FCFE)":
        show_dcf_levered_mode(ticker, persist_data, persist_key)


def show_dcf_fmp_mode(ticker, persist_data, persist_key):
    """DCF fmp mode - uses FMP's DCF with integrated MOS"""
    st.subheader("📊 DCF fmp - FMP Valuation")
    st.write("Get current DCF valuation directly from Financial Modeling Prep.")

    # Parameter input in single row
    mos_percent = (
        st.number_input(
            "Margin of Safety (%)",
            min_value=0.0,
            max_value=75.0,
            value=float(persist_data.get("mos_percent", 25.0)),
            step=5.0,
            key="dcf_fmp_mos",
        )
        / 100
    )

    if st.button("Get DCF Analysis", key="dcf_fmp_run"):
        if not ticker:
            st.error(get_text("please_enter_ticker"))
        else:
            with st.spinner(f"Fetching DCF data for {ticker}..."):
                try:
                    # Save to persistence
                    persist_data_update = {
                        "ticker": ticker,
                        "mos_percent": str(mos_percent * 100),
                    }
                    st.session_state.persist.setdefault(persist_key, {}).update(
                        persist_data_update
                    )
                    save_persistence_data()

                    # Use the enhanced backend function
                    data = dcf_fmp_logic.get_dcf_fmp(ticker, mos_percent)

                    st.success(f"DCF analysis completed for {ticker}")

                    # Main metrics in 4 clean columns like MOS
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        if data.get("dcf"):
                            st.metric(
                                "Fair Value",
                                f"${data['dcf']:,.2f}",
                            )

                    with col2:
                        if data.get("buy_price"):
                            st.metric(
                                f"Buy Price ({mos_percent * 100:.0f}% MOS)",
                                f"${data['buy_price']:,.2f}",
                            )

                    with col3:
                        if data.get("stock_price"):
                            st.metric(
                                "Current Stock Price",
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

                    # Info box like MOS
                    st.info(
                        f"💡 DCF Calculation: Based on FMP DCF valuation | MOS Price = Fair Value × (1 - {mos_percent * 100:.0f}%)"
                    )

                    # Data source info
                    if data.get("as_of"):
                        st.caption(f"📅 Data as of: {data['as_of']}")

                except Exception as e:
                    st.error(f"DCF analysis failed: {str(e)}")


def show_dcf_unlevered_mode(ticker, persist_data, persist_key):
    """DCF Unlevered mode - FCFF methodology with integrated MOS"""
    st.subheader("🏭 Unlevered DCF (FCFF)")
    st.write("Free Cash Flow to Firm - values the entire company before debt.")

    # Main parameters in 4 columns like MOS
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        forecast_years = st.number_input(
            "Forecast Years",
            min_value=3,
            max_value=15,
            value=int(persist_data.get("forecast_years", 5)),
            key="unlevered_years",
        )

    with col2:
        fcff_growth = (
            st.number_input(
                "FCFF Growth (%)",
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
                "WACC (%)",
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
                "Margin of Safety (%)",
                min_value=0.0,
                max_value=75.0,
                value=float(persist_data.get("mos_percent", 25.0)),
                step=5.0,
                key="unlevered_mos",
            )
            / 100
        )

    # Advanced parameters in expander
    with st.expander("Advanced Parameters"):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            perp_growth = (
                st.number_input(
                    "Terminal Growth (%)",
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
                    "Tax Rate (%) - 0 for auto",
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
                "Base Year (optional)",
                min_value=2010,
                max_value=2030,
                value=int(persist_data.get("base_year", 2024)),
                key="unlevered_base_year",
            )

        with col4:
            use_base_year = st.checkbox(
                "Use specific base year", key="unlevered_use_base"
            )

    if st.button("Run Unlevered DCF", key="dcf_unlevered_run"):
        if not ticker:
            st.error(get_text("please_enter_ticker"))
        else:
            with st.spinner(f"Calculating Unlevered DCF for {ticker}..."):
                try:
                    # Save to persistence
                    persist_data_update = {
                        "ticker": ticker,
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

                    st.success(f"Unlevered DCF completed for {ticker}")

                    # Main metrics in 4 clean columns like MOS
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        if result.get("fair_value_per_share"):
                            st.metric(
                                "Fair Value per Share",
                                f"${result['fair_value_per_share']:,.2f}",
                            )

                    with col2:
                        if result.get("buy_price_per_share"):
                            st.metric(
                                f"Buy Price ({mos_percent * 100:.0f}% MOS)",
                                f"${result['buy_price_per_share']:,.2f}",
                            )

                    with col3:
                        if result.get("current_stock_price"):
                            st.metric(
                                "Current Stock Price",
                                f"${result['current_stock_price']:,.2f}",
                            )
                        st.metric(
                            "Enterprise Value",
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

                    # Info box like MOS
                    st.info(
                        f"💡 FCFF Calculation: Based on {fcff_growth * 100:.1f}% growth rate over {forecast_years} years | WACC: {wacc * 100:.1f}% | Terminal: {perp_growth * 100:.1f}%"
                    )

                    # Detailed breakdown in expandable section like MOS
                    with st.expander("📊 Detailed Calculations"):
                        detail_col1, detail_col2 = st.columns(2)

                        with detail_col1:
                            st.metric(
                                "Base FCFF",
                                f"${result.get('fcff0', 0):,.0f}",
                            )
                            st.metric(
                                "PV Explicit FCFF",
                                f"${result.get('pv_explicit', 0):,.0f}",
                            )
                            st.metric(
                                "WACC Used",
                                f"{result.get('wacc', 0) * 100:.1f}%",
                            )

                        with detail_col2:
                            if result.get("pv_terminal"):
                                st.metric(
                                    "PV Terminal Value",
                                    f"${result['pv_terminal']:,.0f}",
                                )
                            st.metric(
                                "Net Debt",
                                f"${result.get('net_debt', 0):,.0f}",
                            )
                            st.metric(
                                "Tax Rate Used",
                                f"{result.get('tax_rate_used', 0) * 100:.1f}%",
                            )

                except Exception as e:
                    st.error(f"Unlevered DCF analysis failed: {str(e)}")


def show_dcf_levered_mode(ticker, persist_data, persist_key):
    """DCF Levered mode - FCFE methodology with integrated MOS"""
    st.subheader("🏦 Levered DCF (FCFE)")
    st.write(
        "Free Cash Flow to Equity - values equity directly including debt effects."
    )

    # Main parameters in 4 columns like MOS
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        forecast_years = st.number_input(
            "Forecast Years",
            min_value=3,
            max_value=15,
            value=int(persist_data.get("forecast_years", 5)),
            key="levered_years",
        )

    with col2:
        fcfe_growth = (
            st.number_input(
                "FCFE Growth (%)",
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
                "Cost of Equity (%)",
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
                "Margin of Safety (%)",
                min_value=0.0,
                max_value=75.0,
                value=float(persist_data.get("mos_percent", 25.0)),
                step=5.0,
                key="levered_mos",
            )
            / 100
        )

    # Advanced parameters in expander
    with st.expander("Advanced Parameters"):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            perp_growth = (
                st.number_input(
                    "Terminal Growth (%)",
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
                "Base Year (optional)",
                min_value=2010,
                max_value=2030,
                value=int(persist_data.get("base_year", 2024)),
                key="levered_base_year",
            )

        with col3:
            use_base_year = st.checkbox(
                "Use specific base year", key="levered_use_base"
            )

        with col4:
            pass  # Empty column for alignment

    if st.button("Run Levered DCF", key="dcf_levered_run"):
        if not ticker:
            st.error(get_text("please_enter_ticker"))
        else:
            with st.spinner(f"Calculating Levered DCF for {ticker}..."):
                try:
                    # Save to persistence
                    persist_data_update = {
                        "ticker": ticker,
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

                    st.success(f"Levered DCF completed for {ticker}")

                    # Main metrics in 4 clean columns like MOS
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        if result.get("fair_value_per_share"):
                            st.metric(
                                "Fair Value per Share",
                                f"${result['fair_value_per_share']:,.2f}",
                            )

                    with col2:
                        if result.get("buy_price_per_share"):
                            st.metric(
                                f"Buy Price ({mos_percent * 100:.0f}% MOS)",
                                f"${result['buy_price_per_share']:,.2f}",
                            )

                    with col3:
                        if result.get("current_stock_price"):
                            st.metric(
                                "Current Stock Price",
                                f"${result['current_stock_price']:,.2f}",
                            )
                        st.metric(
                            "Equity Value",
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

                    # Info box like MOS
                    st.info(
                        f"💡 FCFE Calculation: Based on {fcfe_growth * 100:.1f}% growth rate over {forecast_years} years | Cost of Equity: {cost_of_equity * 100:.1f}% | Terminal: {perp_growth * 100:.1f}%"
                    )

                    # Detailed breakdown in expandable section like MOS
                    with st.expander("📊 Detailed Calculations"):
                        detail_col1, detail_col2 = st.columns(2)

                        with detail_col1:
                            st.metric(
                                "Base FCFE",
                                f"${result.get('fcfe0', 0):,.0f}",
                            )
                            st.metric(
                                "Operating Cash Flow",
                                f"${result.get('cfo', 0):,.0f}",
                            )
                            st.metric(
                                "CapEx",
                                f"${result.get('capex', 0):,.0f}",
                            )

                        with detail_col2:
                            st.metric(
                                "PV Explicit FCFE",
                                f"${result.get('pv_explicit', 0):,.0f}",
                            )
                            if result.get("pv_terminal"):
                                st.metric(
                                    "PV Terminal Value",
                                    f"${result['pv_terminal']:,.0f}",
                                )
                            st.metric(
                                "Net Borrowing",
                                f"${result.get('net_borrowing', 0):,.0f}",
                            )

                except Exception as e:
                    st.error(f"Levered DCF analysis failed: {str(e)}")
