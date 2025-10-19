import streamlit as st
import pandas as pd
from ..config import get_text, save_persistence_data
import backend.logic.pbt as pbt_logic


def show_pbt_analysis():
    """Payback Time Analysis Interface with global ticker support"""

    st.header(f"⏰ {get_text('pbt_title')}")
    st.write(get_text("pbt_description"))

    persist_data = st.session_state.persist.get("PBT", {})

    # Initialisiere global_ticker falls nicht vorhanden - lade aus Persistence
    if "global_ticker" not in st.session_state:
        st.session_state.global_ticker = st.session_state.persist.get(
            "global_ticker", "MSFT"
        )

    # Checkbox für individuellen Ticker
    use_individual_ticker = st.checkbox(
        get_text("use_individual_ticker", "Use individual ticker"),
        value=persist_data.get("use_individual_ticker", False),
        key="pbt_use_individual",
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if use_individual_ticker:
            # Individueller Ticker für dieses Modul
            ticker = st.text_input(
                get_text("ticker_symbol"),
                value=persist_data.get("ticker", ""),
                key="pbt_ticker",
            ).upper()
        else:
            # Globaler Ticker - editierbar und synchronisiert
            ticker = st.text_input(
                get_text("ticker_symbol") + " 🌍",
                value=st.session_state.global_ticker,
                key="pbt_ticker_global",
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

    with col4:
        margin_of_safety = st.number_input(
            get_text("margin_of_safety"),
            min_value=0.0,
            max_value=100.0,
            value=float(persist_data.get("margin_of_safety", 50.0)),
            step=1.0,
            key="pbt_mos",
        )

    if st.button(get_text("run_pbt_analysis"), key="pbt_run_button"):
        if not ticker:
            st.error(get_text("please_enter_ticker"))
        else:
            with st.spinner(get_text("calculating_pbt").format(ticker)):
                try:
                    # Save to persistence
                    persist_data = {
                        "ticker": ticker if use_individual_ticker else "",
                        "use_individual_ticker": use_individual_ticker,
                        "year": str(year),
                        "growth_rate": str(growth_rate),
                        "margin_of_safety": str(margin_of_safety),
                    }
                    st.session_state.persist.setdefault("PBT", {}).update(persist_data)
                    save_persistence_data()

                    # Neue Funktion gibt 4 Werte zurück: fair_value, buy_price, table, price_info
                    fair_value, buy_price, table, price_info = (
                        pbt_logic.calculate_pbt_from_ticker(
                            ticker,
                            year,
                            growth_rate / 100,
                            margin_of_safety / 100,
                            return_full_table=True,
                        )
                    )

                    st.success(get_text("pbt_analysis_completed").format(ticker))

                    # Erweiterte Metriken mit Preisvergleich
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric(
                            get_text("fair_value_8y_payback"), f"${fair_value:,.2f}"
                        )

                    with col2:
                        st.metric(get_text("buy_price_with_mos"), f"${buy_price:,.2f}")

                    with col3:
                        st.metric(
                            get_text("current_stock_price"),
                            f"${price_info['Current Stock Price']:,.2f}",
                        )
                        st.metric(
                            get_text("fcf_per_share"),
                            f"${price_info['FCF per Share']:,.2f}",
                        )

                    with col4:
                        # Bewertung anzeigen (basiert jetzt auf Fair Value)
                        valuation = price_info["Price vs Fair Value"]
                        if "Undervalued" in valuation:
                            st.success(f"📈 {valuation}")
                        elif "Overvalued" in valuation:
                            st.warning(f"📉 {valuation}")
                        else:
                            st.info(f"⚖️ {valuation}")

                        # Investment Recommendation anzeigen
                        recommendation = price_info["Investment Recommendation"]
                        if "Strong Buy" in recommendation:
                            st.success(f"🚀 {recommendation}")
                        elif "Buy" in recommendation:
                            st.success(f"✅ {recommendation}")
                        elif "Hold" in recommendation:
                            st.warning(f"⚖️ {recommendation}")
                        else:
                            st.error(f"❌ {recommendation}")

                    # Zentrale Info-Box mit wichtigen Erklärungen
                    st.info(get_text("pbt_calculation_info").format(margin_of_safety))

                    # Tabelle anzeigen
                    if table:
                        st.subheader(get_text("payback_time_calculation"))
                        df = pd.DataFrame(table)
                        df["Jahr"] = df["Jahr"].astype(int)
                        df = df.rename(
                            columns={
                                "Jahr": get_text("year"),
                                "Einnahme": get_text("income"),
                                "Summe_Cashflows": get_text("cumulative"),
                                "Fair_Value": get_text("fair_value_8y"),
                            }
                        )

                        # Formatierung der Geldbeträge
                        for col in [get_text("income"), get_text("cumulative")]:
                            if col in df.columns:
                                df[col] = df[col].apply(
                                    lambda x: f"${x:,.2f}" if pd.notna(x) else ""
                                )

                        if get_text("fair_value_8y") in df.columns:
                            df[get_text("fair_value_8y")] = df[
                                get_text("fair_value_8y")
                            ].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "")

                        st.dataframe(df, width="stretch")

                except Exception as e:
                    st.error(get_text("pbt_analysis_failed").format(str(e)))
