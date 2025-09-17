import streamlit as st
from ..config import get_text, save_persistence_data
import logic.dcf_lite as dcf_lite_logic


def show_dcf_lite_analysis():
    """DCF Lite Analysis Interface"""
    st.header("💰 DCF Lite Analysis")
    st.write("Get current DCF valuation from Financial Modeling Prep.")

    persist_data = st.session_state.persist.get("DCF_LITE", {})

    ticker = st.text_input(
        "Ticker Symbol", value=persist_data.get("ticker", ""), key="dcf_ticker"
    ).upper()

    if st.button("Get DCF Analysis", key="dcf_run"):
        if not ticker:
            st.error("Please enter a ticker symbol")
        else:
            with st.spinner(f"Fetching DCF data for {ticker}..."):
                try:
                    # Save to persistence
                    persist_data = {"ticker": ticker}
                    st.session_state.persist.setdefault("DCF_LITE", {}).update(
                        persist_data
                    )
                    save_persistence_data()

                    data = dcf_lite_logic.get_dcf_lite(ticker)

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        dcf_value = data.get("dcf")
                        if dcf_value is not None:
                            st.metric("DCF Value", f"${dcf_value:,.2f}")
                        else:
                            st.metric("DCF Value", "N/A")

                    with col2:
                        stock_price = data.get("stock_price")
                        if stock_price is not None:
                            st.metric("Current Stock Price", f"${stock_price:,.2f}")
                        else:
                            st.metric("Current Stock Price", "N/A")

                    with col3:
                        as_of = data.get("as_of")
                        if as_of:
                            st.info(f"As of: {as_of}")

                        # Calculate discount/premium if both values available
                        if dcf_value and stock_price:
                            ratio = (stock_price / dcf_value - 1) * 100
                            if ratio > 0:
                                st.warning(f"Stock is {ratio:.1f}% above DCF")
                            else:
                                st.success(f"Stock is {abs(ratio):.1f}% below DCF")

                    st.success(f"DCF analysis completed for {ticker}")

                except Exception as e:
                    st.error(f"DCF analysis failed: {str(e)}")
