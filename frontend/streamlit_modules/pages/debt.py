import streamlit as st
from ..config import get_text, save_persistence_data
import backend.logic.debt as debt_logic


def show_debt_analysis():
    """Debt Analysis Interface"""
    st.header(f"💳 {get_text('debt_title')}")
    st.write(get_text("debt_description"))

    persist_data = st.session_state.persist.get("DEBT", {})

    # First row: Ticker, Multi-year checkbox, and Debt Type selection
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        ticker = st.text_input(
            get_text("ticker_symbol"),
            value=persist_data.get("ticker", ""),
            key="debt_ticker",
        ).upper()

    with col2:
        multi_year = st.checkbox(
            get_text("multi_year_question"),
            value=persist_data.get("multi_year", False),
            key="debt_multi_year",
        )

    with col3:
        debt_type = st.radio(
            get_text("debt_type_label"),
            options=[get_text("long_term_debt_option"), get_text("total_debt_option")],
            index=0 if persist_data.get("debt_type", "long_term") == "long_term" else 1,
            key="debt_type_radio",
        )
        # Convert display text back to boolean
        use_total_debt = debt_type == get_text("total_debt_option")

    # Second row: Year selection (single or range)
    if multi_year:
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.number_input(
                get_text("from_year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("start_year", 2020)),
                key="debt_start_year",
            )
        with col2:
            end_year = st.number_input(
                get_text("to_year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("end_year", 2024)),
                key="debt_end_year",
            )
    else:
        year = st.number_input(
            get_text("base_year"),
            min_value=1990,
            max_value=2030,
            value=int(persist_data.get("year", 2024)),
            key="debt_year",
        )

    if st.button(get_text("run_debt_analysis"), key="debt_run"):
        if not ticker:
            st.error(get_text("please_enter_ticker"))
        else:
            with st.spinner(get_text("calculating_debt").format(ticker)):
                try:
                    if multi_year:
                        # Save to persistence
                        persist_data = {
                            "ticker": ticker,
                            "multi_year": True,
                            "start_year": str(start_year),
                            "end_year": str(end_year),
                            "debt_type": "total" if use_total_debt else "long_term",
                        }
                        st.session_state.persist.setdefault("DEBT", {}).update(
                            persist_data
                        )
                        save_persistence_data()

                        # Multi-year analysis
                        results = debt_logic.calculate_debt_metrics_multi_year(
                            ticker, start_year, end_year, use_total_debt=use_total_debt
                        )

                        if results:
                            st.success(
                                get_text("debt_analysis_completed").format(ticker)
                            )

                            # Create table data
                            table_data = []
                            for result in results:
                                debt_used = result.get("debt_used", 0)
                                net_income = result.get("net_income", 0)
                                ratio = result.get("debt_to_income_ratio", None)

                                # Determine rating
                                if ratio is not None and net_income > 0:
                                    if ratio < 1:
                                        rating = get_text("debt_rating_excellent")
                                    elif ratio < 2:
                                        rating = get_text("debt_rating_very_good")
                                    elif ratio < 3:
                                        rating = get_text("debt_rating_good")
                                    elif ratio < 5:
                                        rating = get_text("debt_rating_acceptable")
                                    else:
                                        rating = get_text("debt_rating_risky")
                                else:
                                    rating = "N/A"

                                # Use appropriate label based on debt type
                                debt_label = (
                                    get_text("total_debt_mio")
                                    if use_total_debt
                                    else get_text("long_term_debt_mio")
                                )

                                table_data.append(
                                    {
                                        get_text("year"): result.get("year"),
                                        debt_label: f"${debt_used / 1_000_000:,.2f}"
                                        if debt_used
                                        else "$0.00",
                                        get_text(
                                            "net_income_mio"
                                        ): f"${net_income / 1_000_000:,.2f}"
                                        if net_income
                                        else "$0.00",
                                        get_text("debt_to_income_ratio"): f"{ratio:.2f}"
                                        if ratio is not None
                                        else "N/A",
                                        get_text("debt_rating"): rating,
                                    }
                                )

                            # Display table
                            st.dataframe(table_data, use_container_width=True)

                            # Get current price for comparison (using latest year)
                            try:
                                current_price = debt_logic.fmp_api.get_current_price(
                                    ticker
                                )
                                if current_price:
                                    st.info(
                                        f"📊 {get_text('current_stock_price')}: ${current_price:,.2f}"
                                    )
                            except Exception:
                                pass

                            # Info note
                            debt_type_text = (
                                get_text("total_debt_option")
                                if use_total_debt
                                else get_text("long_term_debt_option")
                            )
                            st.info(
                                f"💡 {get_text('debt_multi_year_info_with_type').format(debt_type_text, start_year, end_year)}"
                            )

                        else:
                            st.warning(get_text("no_valid_data"))

                    else:
                        # Save to persistence
                        persist_data = {
                            "ticker": ticker,
                            "multi_year": False,
                            "year": str(year),
                            "debt_type": "total" if use_total_debt else "long_term",
                        }
                        st.session_state.persist.setdefault("DEBT", {}).update(
                            persist_data
                        )
                        save_persistence_data()

                        # Single year analysis
                        result = debt_logic.calculate_debt_metrics_from_ticker(
                            ticker, year, use_total_debt=use_total_debt
                        )

                        if result:
                            st.success(
                                get_text("debt_analysis_completed").format(ticker)
                            )

                            # Main metrics in 3 columns
                            col1, col2, col3 = st.columns(3)

                            debt_used = result.get("debt_used", 0)
                            net_income = result.get("net_income", 0)
                            ratio = result.get("debt_to_income_ratio", None)

                            # Use appropriate label based on debt type
                            debt_label = (
                                get_text("total_debt")
                                if use_total_debt
                                else get_text("long_term_debt")
                            )

                            with col1:
                                st.metric(
                                    debt_label,
                                    f"${debt_used / 1_000_000:,.2f}M"
                                    if debt_used
                                    else "$0.00M",
                                )

                            with col2:
                                st.metric(
                                    get_text("net_income"),
                                    f"${net_income / 1_000_000:,.2f}M"
                                    if net_income
                                    else "$0.00M",
                                )

                            with col3:
                                if ratio is not None:
                                    st.metric(
                                        get_text("debt_to_income_ratio"),
                                        f"{ratio:.2f}",
                                    )
                                else:
                                    st.metric(
                                        get_text("debt_to_income_ratio"),
                                        "N/A",
                                    )

                            # Rating section
                            if ratio is not None and net_income > 0:
                                st.markdown("---")

                                # Determine rating
                                if ratio < 1:
                                    rating = get_text("debt_rating_excellent")
                                    color = "🟢"
                                    status = "success"
                                elif ratio < 2:
                                    rating = get_text("debt_rating_very_good")
                                    color = "🟢"
                                    status = "success"
                                elif ratio < 3:
                                    rating = get_text("debt_rating_good")
                                    color = "🟡"
                                    status = "info"
                                elif ratio < 5:
                                    rating = get_text("debt_rating_acceptable")
                                    color = "🟡"
                                    status = "warning"
                                else:
                                    rating = get_text("debt_rating_risky")
                                    color = "🔴"
                                    status = "error"

                                # Display rating
                                if status == "success":
                                    st.success(f"{color} {rating}")
                                elif status == "info":
                                    st.info(f"{color} {rating}")
                                elif status == "warning":
                                    st.warning(f"{color} {rating}")
                                else:
                                    st.error(f"{color} {rating}")

                                # Info box with interpretation
                                st.info(f"💡 {get_text('debt_info_explanation')}")

                            elif net_income <= 0:
                                st.warning(
                                    f"⚠️ {get_text('debt_negative_income_warning')}"
                                )

                            # Detailed breakdown in expander
                            with st.expander(f"📊 {get_text('debt_detailed_info')}"):
                                st.write(get_text("debt_threshold_explanation"))

                                thresholds = [
                                    ("< 1.0", get_text("debt_rating_excellent")),
                                    ("1.0 - 2.0", get_text("debt_rating_very_good")),
                                    ("2.0 - 3.0", get_text("debt_rating_good")),
                                    ("3.0 - 5.0", get_text("debt_rating_acceptable")),
                                    ("> 5.0", get_text("debt_rating_risky")),
                                ]

                                for threshold, description in thresholds:
                                    st.write(f"**{threshold}**: {description}")

                        else:
                            st.warning(get_text("no_valid_data"))

                except Exception as e:
                    st.error(get_text("debt_analysis_failed").format(str(e)))
