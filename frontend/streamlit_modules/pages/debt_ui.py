import streamlit as st
from ..config import get_text, save_persistence_data
import backend.logic.debt as debt_logic


def _get_rating_from_ratio(ratio):
    """Helper function to get rating text from ratio"""
    if ratio is None:
        return "N/A", "info"
    if ratio < 1:
        return get_text("debt.rating_excellent"), "success"
    elif ratio < 2:
        return get_text("debt.rating_very_good"), "success"
    elif ratio < 3:
        return get_text("debt.rating_good"), "info"
    elif ratio < 5:
        return get_text("debt.rating_acceptable"), "warning"
    else:
        return get_text("debt.rating_risky"), "error"


def show_debt_analysis():
    """Debt Analysis Interface with global ticker support"""
    st.header(f"💳 {get_text('debt.title')}")
    st.write(get_text("debt.description"))

    persist_data = st.session_state.persist.get("DEBT", {})

    if "global_ticker" not in st.session_state:
        st.session_state.global_ticker = st.session_state.persist.get(
            "global_ticker", "MSFT"
        )

    use_individual_ticker = st.checkbox(
        get_text("common.use_individual_ticker"),
        value=persist_data.get("use_individual_ticker", False),
        key="debt_use_individual",
    )

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if use_individual_ticker:
            ticker = st.text_input(
                get_text("common.ticker_symbol"),
                value=persist_data.get("ticker", ""),
                key="debt_ticker",
            ).upper()
        else:
            ticker = st.text_input(
                get_text("common.ticker_symbol") + " 🌍",
                value=st.session_state.global_ticker,
                key="debt_ticker_global",
                help=get_text("common.global_ticker_help"),
            ).upper()
            if ticker != st.session_state.global_ticker:
                st.session_state.global_ticker = ticker

    with col2:
        multi_year = st.checkbox(
            get_text("common.multi_year_checkbox"),
            value=persist_data.get("multi_year", True),
            key="debt_multi_year",
        )

    with col3:
        debt_type = st.radio(
            get_text("debt.debt_type_label"),
            options=[
                get_text("debt.long_term_debt_option"),
                get_text("debt.total_debt_option"),
            ],
            index=0 if persist_data.get("debt_type", "long_term") == "long_term" else 1,
            key="debt_type_radio",
        )
        use_total_debt = debt_type == get_text("debt.total_debt_option")

    if multi_year:
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.number_input(
                get_text("common.start_year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("start_year", 2020)),
                key="debt_start_year",
            )
        with col2:
            end_year = st.number_input(
                get_text("common.end_year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("end_year", 2024)),
                key="debt_end_year",
            )
    else:
        year = st.number_input(
            get_text("common.year"),
            min_value=1990,
            max_value=2030,
            value=int(persist_data.get("year", 2024)),
            key="debt_year",
        )

    if st.button(get_text("debt.run_analysis"), key="debt_run"):
        if not ticker:
            st.error(get_text("common.please_enter_ticker"))
        else:
            with st.spinner(get_text("debt.calculating").format(ticker)):
                try:
                    if multi_year:
                        persist_data = {
                            "ticker": ticker if use_individual_ticker else "",
                            "use_individual_ticker": use_individual_ticker,
                            "multi_year": True,
                            "start_year": str(start_year),
                            "end_year": str(end_year),
                            "debt_type": "total" if use_total_debt else "long_term",
                        }
                        st.session_state.persist.setdefault("DEBT", {}).update(
                            persist_data
                        )
                        save_persistence_data()

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
                                get_text("debt.analysis_completed").format(ticker)
                            )

                            table_data = []
                            for i, result in enumerate(results_income):
                                debt_used = result.get("debt_used", 0)

                                ratio_income = result.get("debt_ratio", None)
                                ratio_ebitda = results_ebitda[i].get("debt_ratio", None)
                                ratio_cf = results_cf[i].get("debt_ratio", None)

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
                                    get_text("debt.total_debt_mio")
                                    if use_total_debt
                                    else get_text("debt.long_term_debt_mio")
                                )

                                table_data.append(
                                    {
                                        get_text("common.year"): result.get("year"),
                                        debt_label: f"${debt_used / 1_000_000:,.2f}"
                                        if debt_used
                                        else "$0.00",
                                        get_text(
                                            "debt.income_ratio"
                                        ): f"{ratio_income:.2f}"
                                        if ratio_income is not None
                                        else "N/A",
                                        get_text(
                                            "debt.ebitda_ratio"
                                        ): f"{ratio_ebitda:.2f}"
                                        if ratio_ebitda is not None
                                        else "N/A",
                                        get_text("debt.cf_ratio"): f"{ratio_cf:.2f}"
                                        if ratio_cf is not None
                                        else "N/A",
                                        get_text("debt.rating"): rating,
                                    }
                                )

                            st.dataframe(
                                table_data, use_container_width=True, hide_index=True
                            )

                            try:
                                current_price = debt_logic.fmp_api.get_current_price(
                                    ticker
                                )
                                if current_price:
                                    st.info(
                                        f"📊 {get_text('common.current_stock_price')}: ${current_price:,.2f}"
                                    )
                            except Exception:
                                pass

                            debt_type_text = (
                                get_text("debt.total_debt_option")
                                if use_total_debt
                                else get_text("debt.long_term_debt_option")
                            )
                            st.info(
                                f"💡 {get_text('debt.multi_year_info_with_type').format(debt_type_text, start_year, end_year)}"
                            )

                        else:
                            st.warning(get_text("common.no_valid_data"))

                    else:
                        persist_data = {
                            "ticker": ticker if use_individual_ticker else "",
                            "use_individual_ticker": use_individual_ticker,
                            "multi_year": False,
                            "year": str(year),
                            "debt_type": "total" if use_total_debt else "long_term",
                        }
                        st.session_state.persist.setdefault("DEBT", {}).update(
                            persist_data
                        )
                        save_persistence_data()

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
                                get_text("debt.analysis_completed").format(ticker)
                            )

                            debt_used = result_income.get("debt_used", 0)
                            debt_label = (
                                get_text("debt.total_debt")
                                if use_total_debt
                                else get_text("debt.long_term_debt")
                            )

                            st.subheader(
                                f"{debt_label}: ${debt_used / 1_000_000:,.2f}M"
                            )
                            st.markdown("---")

                            col1, col2, col3 = st.columns(3)

                            ratio_income = result_income.get("debt_ratio", None)
                            ratio_ebitda = result_ebitda.get("debt_ratio", None)
                            ratio_cf = result_cf.get("debt_ratio", None)

                            with col1:
                                st.metric(
                                    get_text("debt.income_ratio"),
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
                                    get_text("debt.ebitda_ratio"),
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
                                    get_text("debt.cf_ratio"),
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

                            with st.expander(f"📊 {get_text('debt.detailed_values')}"):
                                col1, col2, col3 = st.columns(3)

                                net_income = result_income.get("net_income", 0)
                                ebitda = result_ebitda.get("ebitda", 0)
                                op_cf = result_cf.get("operating_cash_flow", 0)

                                with col1:
                                    st.metric(
                                        get_text("debt.net_income"),
                                        f"${net_income / 1_000_000:,.2f}M",
                                    )
                                with col2:
                                    st.metric(
                                        get_text("debt.ebitda"),
                                        f"${ebitda / 1_000_000:,.2f}M",
                                    )
                                with col3:
                                    st.metric(
                                        get_text("debt.operating_cash_flow"),
                                        f"${op_cf / 1_000_000:,.2f}M",
                                    )

                            st.info(f"💡 {get_text('debt.info_explanation_multi')}")

                            with st.expander(f"📊 {get_text('debt.detailed_info')}"):
                                st.write(get_text("debt.threshold_explanation"))

                                thresholds = [
                                    ("< 1.0", get_text("debt.rating_excellent")),
                                    ("1.0 - 2.0", get_text("debt.rating_very_good")),
                                    ("2.0 - 3.0", get_text("debt.rating_good")),
                                    ("3.0 - 5.0", get_text("debt.rating_acceptable")),
                                    ("> 5.0", get_text("debt.rating_risky")),
                                ]

                                for threshold, description in thresholds:
                                    st.write(f"**{threshold}**: {description}")

                        else:
                            st.warning(get_text("common.no_valid_data"))

                except Exception as e:
                    st.error(get_text("debt.analysis_failed").format(str(e)))
