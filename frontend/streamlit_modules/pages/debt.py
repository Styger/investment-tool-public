import streamlit as st
from ..config import get_text, save_persistence_data
import backend.logic.debt as debt_logic


def show_debt_analysis():
    """Debt Analysis Interface"""
    st.header(f"💳 {get_text('debt_title')}")
    st.write(get_text("debt_description"))

    col1, col2 = st.columns(2)

    persist_data = st.session_state.persist.get("DEBT", {})

    with col1:
        ticker = st.text_input(
            get_text("ticker_symbol"),
            value=persist_data.get("ticker", ""),
            key="debt_ticker",
        ).upper()

    with col2:
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
                    # Save to persistence
                    persist_data = {
                        "ticker": ticker,
                        "year": str(year),
                    }
                    st.session_state.persist.setdefault("DEBT", {}).update(persist_data)
                    save_persistence_data()

                    result = debt_logic.calculate_debt_metrics_from_ticker(ticker, year)

                    if result:
                        st.success(get_text("debt_analysis_completed").format(ticker))

                        # Main metrics in 3 columns
                        col1, col2, col3 = st.columns(3)

                        long_term_debt = result.get("long_term_debt", 0)
                        net_income = result.get("net_income", 0)
                        ratio = result.get("debt_to_income_ratio", None)

                        with col1:
                            st.metric(
                                get_text("long_term_debt"),
                                f"${long_term_debt / 1_000_000:,.2f}M"
                                if long_term_debt
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
                            st.warning(f"⚠️ {get_text('debt_negative_income_warning')}")

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
