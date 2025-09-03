import streamlit as st
import pandas as pd
from ..config import get_text, save_persistence_data
import logic.pbt as pbt_logic


def show_pbt_analysis():
    """Payback Time Analysis Interface"""

    st.header(f"⏰ {get_text('pbt_title')}")
    st.write(get_text("pbt_description"))

    col1, col2, col3 = st.columns(3)

    persist_data = st.session_state.persist.get("PBT", {})

    with col1:
        ticker = st.text_input(
            get_text("ticker_symbol"),
            value=persist_data.get("ticker", ""),
            key="pbt_ticker",
        ).upper()

    with col2:
        year = st.number_input(
            get_text("base_year"),
            min_value=1990,
            max_value=2030,
            value=int(persist_data.get("year", 2024)),
            key="pbt_year",
        )

    with col3:
        growth_rate = st.number_input(
            get_text("growth_rate"),
            min_value=0.0,
            max_value=100.0,
            value=float(persist_data.get("growth_rate", 13.0)),
            step=0.1,
            key="pbt_growth",
        )

    if st.button(get_text("run_pbt_analysis"), key="pbt_run_button"):
        if not ticker:
            st.error(get_text("please_enter_ticker"))
        else:
            with st.spinner(get_text("calculating_pbt").format(ticker)):
                try:
                    # Save to persistence
                    persist_data = {
                        "ticker": ticker,
                        "year": str(year),
                        "growth_rate": str(growth_rate),
                    }
                    st.session_state.persist.setdefault("PBT", {}).update(persist_data)
                    save_persistence_data()

                    # Neue Funktion gibt 3 Werte zurück: price, table, price_info
                    price, table, price_info = pbt_logic.calculate_pbt_from_ticker(
                        ticker, year, growth_rate / 100, return_full_table=True
                    )

                    st.success(get_text("pbt_analysis_completed").format(ticker))

                    # Erweiterte Metriken mit Preisvergleich
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(get_text("pbt_buy_price"), f"${price:,.2f}")
                        st.info(get_text("based_on_8_year_payback"))

                    with col2:
                        st.metric(
                            "Current Stock Price",
                            f"${price_info['Current Stock Price']:,.2f}",
                        )
                        st.metric(
                            "FCF per Share", f"${price_info['FCF per Share']:,.2f}"
                        )

                    with col3:
                        # Bewertung anzeigen
                        valuation = price_info["Price vs PBT"]
                        if "Undervalued" in valuation:
                            st.success(f"📈 {valuation}")
                        elif "Overvalued" in valuation:
                            st.warning(f"📉 {valuation}")
                        else:
                            st.info(f"⚖️ {valuation}")

                        st.metric(
                            "Percentage Difference",
                            f"{price_info['Percentage Difference']:+.1f}%",
                        )

                    # Tabelle anzeigen
                    if table:
                        st.subheader("Payback Time Calculation")
                        df = pd.DataFrame(table)
                        df["Jahr"] = df["Jahr"].astype(int)
                        df = df.rename(
                            columns={
                                "Jahr": get_text("year"),
                                "Einnahme": get_text("income"),
                                "Summe_Cashflows": get_text("cumulative"),
                                "PBT_Preis": "PBT Price",
                            }
                        )

                        # Formatierung der Geldbeträge
                        for col in [get_text("income"), get_text("cumulative")]:
                            if col in df.columns:
                                df[col] = df[col].apply(
                                    lambda x: f"${x:,.2f}" if pd.notna(x) else ""
                                )

                        if "PBT Price" in df.columns:
                            df["PBT Price"] = df["PBT Price"].apply(
                                lambda x: f"${x:,.2f}" if pd.notna(x) else ""
                            )

                        st.dataframe(df, use_container_width=True)

                except Exception as e:
                    st.error(get_text("pbt_analysis_failed").format(str(e)))
