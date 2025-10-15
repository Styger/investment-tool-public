import streamlit as st
from ..config import get_text, save_persistence_data
import backend.logic.debt as debt_logic


def _get_rating_from_ratio(ratio):
    """Helper function to get rating text from ratio"""
    if ratio is None:
        return "N/A", "info"
    if ratio < 1:
        return get_text("debt_rating_excellent"), "success"
    elif ratio < 2:
        return get_text("debt_rating_very_good"), "success"
    elif ratio < 3:
        return get_text("debt_rating_good"), "info"
    elif ratio < 5:
        return get_text("debt_rating_acceptable"), "warning"
    else:
        return get_text("debt_rating_risky"), "error"


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
            value=persist_data.get("multi_year", True),
            key="debt_multi_year",
        )

    with col3:
        debt_type = st.radio(
            get_text("debt_type_label"),
            options=[get_text("long_term_debt_option"), get_text("total_debt_option")],
            index=0 if persist_data.get("debt_type", "long_term") == "long_term" else 1,
            key="debt_type_radio",
        )
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

                        # Fetch results for all 3 metrics
                        results_income = debt_logic.calculate_debt_metrics_multi_year(
                            ticker,
                            start_year,
                            end_year,
                            use_total_debt=use_total_debt,
                            metric_type="net_income",
                        )
                        results_ebitda = debt_logic.calculate_debt_metrics_multi_year(
                            ticker,
                            start_year,
                            end_year,
                            use_total_debt=use_total_debt,
                            metric_type="ebitda",
                        )
                        results_cf = debt_logic.calculate_debt_metrics_multi_year(
                            ticker,
                            start_year,
                            end_year,
                            use_total_debt=use_total_debt,
                            metric_type="operating_cash_flow",
                        )

                        if results_income:
                            st.success(
                                get_text("debt_analysis_completed").format(ticker)
                            )

                            # Create table data with all 3 ratios
                            table_data = []
                            for i, result in enumerate(results_income):
                                debt_used = result.get("debt_used", 0)

                                ratio_income = result.get("debt_ratio", None)
                                ratio_ebitda = results_ebitda[i].get("debt_ratio", None)
                                ratio_cf = results_cf[i].get("debt_ratio", None)

                                # Average rating based on all 3 ratios
                                ratios = [
                                    r
                                    for r in [ratio_income, ratio_ebitda, ratio_cf]
                                    if r is not None
                                ]
                                if ratios:
                                    avg_ratio = sum(ratios) / len(ratios)
                                    rating, _ = _get_rating_from_ratio(avg_ratio)
                                else:
                                    rating = "N/A"

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
                                            "debt_income_ratio"
                                        ): f"{ratio_income:.2f}"
                                        if ratio_income is not None
                                        else "N/A",
                                        get_text(
                                            "debt_ebitda_ratio"
                                        ): f"{ratio_ebitda:.2f}"
                                        if ratio_ebitda is not None
                                        else "N/A",
                                        get_text("debt_cf_ratio"): f"{ratio_cf:.2f}"
                                        if ratio_cf is not None
                                        else "N/A",
                                        get_text("debt_rating"): rating,
                                    }
                                )

                            # Display table
                            st.dataframe(table_data, use_container_width=True)

                            # Get current price for comparison
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

                        # Single year analysis - fetch all 3 metrics
                        result_income = debt_logic.calculate_debt_metrics_from_ticker(
                            ticker,
                            year,
                            use_total_debt=use_total_debt,
                            metric_type="net_income",
                        )
                        result_ebitda = debt_logic.calculate_debt_metrics_from_ticker(
                            ticker,
                            year,
                            use_total_debt=use_total_debt,
                            metric_type="ebitda",
                        )
                        result_cf = debt_logic.calculate_debt_metrics_from_ticker(
                            ticker,
                            year,
                            use_total_debt=use_total_debt,
                            metric_type="operating_cash_flow",
                        )

                        if result_income:
                            st.success(
                                get_text("debt_analysis_completed").format(ticker)
                            )

                            # Display debt amount
                            debt_used = result_income.get("debt_used", 0)
                            debt_label = (
                                get_text("total_debt")
                                if use_total_debt
                                else get_text("long_term_debt")
                            )

                            st.subheader(
                                f"{debt_label}: ${debt_used / 1_000_000:,.2f}M"
                            )
                            st.markdown("---")

                            # All 3 ratios in columns
                            col1, col2, col3 = st.columns(3)

                            ratio_income = result_income.get("debt_ratio", None)
                            ratio_ebitda = result_ebitda.get("debt_ratio", None)
                            ratio_cf = result_cf.get("debt_ratio", None)

                            with col1:
                                st.metric(
                                    get_text("debt_income_ratio"),
                                    f"{ratio_income:.2f}"
                                    if ratio_income is not None
                                    else "N/A",
                                )
                                rating, status = _get_rating_from_ratio(ratio_income)
                                if status == "success":
                                    st.success(f"🟢 {rating}")
                                elif status == "info":
                                    st.info(f"🟡 {rating}")
                                elif status == "warning":
                                    st.warning(f"🟡 {rating}")
                                elif status == "error":
                                    st.error(f"🔴 {rating}")

                            with col2:
                                st.metric(
                                    get_text("debt_ebitda_ratio"),
                                    f"{ratio_ebitda:.2f}"
                                    if ratio_ebitda is not None
                                    else "N/A",
                                )
                                rating, status = _get_rating_from_ratio(ratio_ebitda)
                                if status == "success":
                                    st.success(f"🟢 {rating}")
                                elif status == "info":
                                    st.info(f"🟡 {rating}")
                                elif status == "warning":
                                    st.warning(f"🟡 {rating}")
                                elif status == "error":
                                    st.error(f"🔴 {rating}")

                            with col3:
                                st.metric(
                                    get_text("debt_cf_ratio"),
                                    f"{ratio_cf:.2f}"
                                    if ratio_cf is not None
                                    else "N/A",
                                )
                                rating, status = _get_rating_from_ratio(ratio_cf)
                                if status == "success":
                                    st.success(f"🟢 {rating}")
                                elif status == "info":
                                    st.info(f"🟡 {rating}")
                                elif status == "warning":
                                    st.warning(f"🟡 {rating}")
                                elif status == "error":
                                    st.error(f"🔴 {rating}")

                            # Detailed values in expander
                            with st.expander(f"📊 {get_text('debt_detailed_values')}"):
                                col1, col2, col3 = st.columns(3)

                                net_income = result_income.get("net_income", 0)
                                ebitda = result_ebitda.get("ebitda", 0)
                                op_cf = result_cf.get("operating_cash_flow", 0)

                                with col1:
                                    st.metric(
                                        get_text("net_income"),
                                        f"${net_income / 1_000_000:,.2f}M",
                                    )
                                with col2:
                                    st.metric(
                                        get_text("ebitda"),
                                        f"${ebitda / 1_000_000:,.2f}M",
                                    )
                                with col3:
                                    st.metric(
                                        get_text("operating_cash_flow"),
                                        f"${op_cf / 1_000_000:,.2f}M",
                                    )

                            # Info box with interpretation
                            st.info(f"💡 {get_text('debt_info_explanation_multi')}")

                            # Threshold explanation in expander
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
