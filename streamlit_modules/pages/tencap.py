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

                    if show_details:
                        # Details anzeigen - zurück zur ursprünglichen Methode mit capture_output
                        for year in years:
                            try:
                                _, output = capture_output(
                                    tencap_logic.print_ten_cap_analysis,
                                    ticker,
                                    year,
                                    tencap_logic.language,  # Verwende das language dict aus tencap_logic
                                )
                                if output.strip():
                                    st.code(
                                        output, language=None
                                    )  # st.code statt st.text für bessere Formatierung
                                else:
                                    st.warning(f"Keine Details für {year} verfügbar")
                            except Exception as e:
                                st.error(f"Fehler bei {year}: {str(e)}")
                    else:
                        # Tabellen-Ansicht
                        results = []
                        latest_year = max(years)
                        current_price_data = None

                        # Hole Current Price vom neuesten Jahr
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
                                    "comparison": latest_result.get(
                                        "price_vs_ten_cap", "N/A"
                                    ),
                                }
                        except Exception as e:
                            st.warning(f"Could not fetch current price: {str(e)}")

                        # Sammle alle Ergebnisse
                        for year in years:
                            try:
                                result_data = (
                                    tencap_logic.calculate_ten_cap_with_comparison(
                                        ticker, year
                                    )
                                )

                                if result_data:
                                    ten_cap_price = result_data.get("ten_cap_buy_price")

                                    row = {
                                        get_text("year"): year,
                                        get_text(
                                            "ten_cap_price"
                                        ): f"${ten_cap_price:,.2f}"
                                        if ten_cap_price
                                        else "N/A",
                                    }

                                    # Current Price nur beim neuesten Jahr hinzufügen
                                    if year == latest_year and current_price_data:
                                        row["Current Price"] = (
                                            f"${current_price_data['price']:,.2f}"
                                        )
                                        row["Price vs TEN CAP"] = current_price_data[
                                            "comparison"
                                        ]

                                    results.append(row)
                                else:
                                    results.append(
                                        {
                                            get_text("year"): year,
                                            get_text("ten_cap_price"): "N/A",
                                        }
                                    )

                            except Exception as e:
                                results.append(
                                    {
                                        get_text("year"): year,
                                        get_text("ten_cap_price"): f"Error: {str(e)}",
                                    }
                                )

                        if results:
                            # Spezielle Anzeige für Single Year
                            if len(years) == 1 and current_price_data:
                                st.subheader(f"TEN CAP Analysis for {ticker}")

                                # Metriken in Spalten anzeigen
                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    st.metric(
                                        "TEN CAP Buy Price",
                                        results[0][get_text("ten_cap_price")],
                                    )

                                with col2:
                                    st.metric(
                                        "Current Stock Price",
                                        f"${current_price_data['price']:,.2f}",
                                    )

                                with col3:
                                    valuation = current_price_data["comparison"]
                                    if "Undervalued" in valuation:
                                        st.success(f"📈 {valuation}")
                                    elif "Overvalued" in valuation:
                                        st.warning(f"📉 {valuation}")
                                    else:
                                        st.info(f"⚖️ {valuation}")

                            # Tabelle für alle Fälle anzeigen
                            df = pd.DataFrame(results)
                            st.dataframe(df, use_container_width=True)

                            # Zusätzliche Info bei Multi-Year
                            if multi_year and current_price_data:
                                st.info(
                                    f"Current price comparison is based on the latest year ({latest_year}) data."
                                )

                    st.success(get_text("tencap_analysis_completed").format(ticker))

                except Exception as e:
                    st.error(get_text("tencap_analysis_failed").format(str(e)))
