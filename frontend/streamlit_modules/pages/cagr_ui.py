import streamlit as st
from ..config import get_text, save_persistence_data, capture_output
import backend.logic.cagr
import pandas as pd


def show_cagr_analysis():
    """CAGR Analysis Interface with global ticker support"""
    st.header(f"📈 {get_text('cagr.title')}")
    st.write(get_text("cagr.description"))

    # Load persisted values
    persist_data = st.session_state.persist.get("CAGR", {})

    # Safety check: Stelle sicher, dass persist_data ein Dictionary ist
    if not isinstance(persist_data, dict):
        persist_data = {}

    # Initialisiere global_ticker falls nicht vorhanden - lade aus Persistence
    if "global_ticker" not in st.session_state:
        global_ticker_value = st.session_state.persist.get("global_ticker", "MSFT")
        # Safety check für global_ticker
        if isinstance(global_ticker_value, str):
            st.session_state.global_ticker = global_ticker_value
        else:
            st.session_state.global_ticker = "MSFT"

    # Checkbox für individuellen Ticker
    use_individual_ticker = st.checkbox(
        get_text("common.use_individual_ticker"),
        value=persist_data.get("use_individual_ticker", False),
        key="cagr_use_individual",
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if use_individual_ticker:
            # Individueller Ticker für dieses Modul
            ticker = st.text_input(
                get_text("common.ticker_symbol"),
                value=persist_data.get("ticker", ""),
                key="cagr_ticker",
            ).upper()
        else:
            # Globaler Ticker - editierbar und synchronisiert
            ticker = st.text_input(
                get_text("common.ticker_symbol") + " 🌍",
                value=st.session_state.global_ticker,
                key="cagr_ticker_global",
                help=get_text("common.global_ticker_help"),
            ).upper()
            # Update global ticker wenn geändert
            if ticker != st.session_state.global_ticker:
                st.session_state.global_ticker = ticker
                # Speichere globalen Ticker in Persistence
                st.session_state.persist["global_ticker"] = ticker
                save_persistence_data()

    with col2:
        start_year = st.number_input(
            get_text("common.start_year"),
            min_value=1990,
            max_value=2030,
            value=int(persist_data.get("start_year", 2018)),
            key="cagr_start",
        )

    with col3:
        end_year = st.number_input(
            get_text("common.end_year"),
            min_value=1990,
            max_value=2030,
            value=int(persist_data.get("end_year", 2024)),
            key="cagr_end",
        )

    with col4:
        period_years = st.number_input(
            get_text("cagr.period_years"),
            min_value=1,
            max_value=20,
            value=int(persist_data.get("period_years", 5)),
            key="cagr_period",
        )

    # Metric selection checkboxes - JETZT 5 SPALTEN
    st.markdown(f"**{get_text('cagr.select_metrics')}**")
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)

    with col_m1:
        include_book = st.checkbox(
            get_text("cagr.checkbox_book"),
            value=persist_data.get("include_book", True),
            key="cagr_book",
        )

    with col_m2:
        include_eps = st.checkbox(
            get_text("cagr.checkbox_eps"),
            value=persist_data.get("include_eps", True),
            key="cagr_eps",
        )

    with col_m3:
        include_revenue = st.checkbox(
            get_text("cagr.checkbox_revenue"),
            value=persist_data.get("include_revenue", True),
            key="cagr_revenue",
        )

    with col_m4:
        include_cashflow = st.checkbox(
            get_text("cagr.checkbox_cashflow"),
            value=persist_data.get("include_cashflow", True),
            key="cagr_cashflow",
        )

    with col_m5:
        include_fcf = st.checkbox(
            get_text("cagr.checkbox_fcf"),
            value=persist_data.get("include_fcf", True),
            key="cagr_fcf",
        )

    if st.button(get_text("cagr.run_analysis"), key="cagr_run"):
        if not ticker:
            st.error(get_text("common.please_enter_ticker"))
        elif start_year >= end_year:
            st.error(get_text("common.start_year_before_end"))
        elif not any(
            [include_book, include_eps, include_revenue, include_cashflow, include_fcf]
        ):
            st.error(get_text("cagr.select_at_least_one_metric"))
        else:
            with st.spinner(get_text("common.analyzing").format(ticker)):
                try:
                    # Save to persistence
                    persist_data = {
                        "ticker": ticker if use_individual_ticker else "",
                        "use_individual_ticker": use_individual_ticker,
                        "start_year": str(start_year),
                        "end_year": str(end_year),
                        "period_years": str(period_years),
                        "include_book": include_book,
                        "include_eps": include_eps,
                        "include_revenue": include_revenue,
                        "include_cashflow": include_cashflow,
                        "include_fcf": include_fcf,
                    }
                    st.session_state.persist.setdefault("CAGR", {}).update(persist_data)
                    save_persistence_data()

                    _, output = capture_output(
                        backend.logic.cagr.run_analysis,
                        ticker,
                        start_year,
                        end_year,
                        period_years,
                        include_book,
                        include_eps,
                        include_revenue,
                        include_cashflow,
                        include_fcf,
                    )

                    if output.strip():
                        st.success(get_text("common.analysis_completed").format(ticker))

                        # Parse the output to create a proper table
                        lines = output.strip().split("\n")
                        data_rows = []

                        for line in lines:
                            if line.strip() and any(char.isdigit() for char in line):
                                parts = line.split()
                                if len(parts) >= 3 and parts[0].isdigit():
                                    try:
                                        row = {
                                            get_text("common.from_year"): int(parts[0]),
                                            get_text("common.to_year"): int(parts[1]),
                                        }

                                        # Dynamically add columns based on selected metrics
                                        col_idx = 2
                                        if include_book:
                                            row["Book"] = (
                                                f"{float(parts[col_idx]):.2f}%"
                                            )
                                            col_idx += 1
                                        if include_eps:
                                            row["EPS"] = f"{float(parts[col_idx]):.2f}%"
                                            col_idx += 1
                                        if include_revenue:
                                            row[get_text("common.revenue")] = (
                                                f"{float(parts[col_idx]):.2f}%"
                                            )
                                            col_idx += 1
                                        if include_cashflow:
                                            row["Cashflow"] = (
                                                f"{float(parts[col_idx]):.2f}%"
                                            )
                                            col_idx += 1
                                        if include_fcf:
                                            row["FCF"] = f"{float(parts[col_idx]):.2f}%"
                                            col_idx += 1

                                        # Average is always last
                                        row[get_text("cagr.average")] = (
                                            f"{float(parts[col_idx]):.2f}%"
                                        )
                                        data_rows.append(row)
                                    except (ValueError, IndexError):
                                        continue

                        if data_rows:
                            df = pd.DataFrame(data_rows)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                        else:
                            st.text(output)
                    else:
                        st.warning(get_text("common.no_output_generated"))

                except Exception as e:
                    st.error(get_text("common.analysis_failed").format(str(e)))
