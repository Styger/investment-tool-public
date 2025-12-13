import streamlit as st
from ..config import get_text, save_persistence_data
import backend.logic.profitability as profitability_logic


def _get_return_rating(ratio, metric_type):
    """Helper function to get rating for return ratios (ROE, ROA)"""
    if ratio is None:
        return "N/A", "info"

    if metric_type == "roe":
        if ratio >= 0.20:
            return get_text("profitability.rating_excellent"), "success"
        elif ratio >= 0.15:
            return get_text("profitability.rating_very_good"), "success"
        elif ratio >= 0.10:
            return get_text("profitability.rating_good"), "info"
        elif ratio >= 0.05:
            return get_text("profitability.rating_acceptable"), "warning"
        else:
            return get_text("profitability.rating_poor"), "error"

    elif metric_type == "roa":
        if ratio >= 0.10:
            return get_text("profitability.rating_excellent"), "success"
        elif ratio >= 0.07:
            return get_text("profitability.rating_very_good"), "success"
        elif ratio >= 0.05:
            return get_text("profitability.rating_good"), "info"
        elif ratio >= 0.03:
            return get_text("profitability.rating_acceptable"), "warning"
        else:
            return get_text("profitability.rating_poor"), "error"

    elif metric_type == "roic":
        if ratio >= 0.15:
            return get_text("profitability.rating_excellent"), "success"
        elif ratio >= 0.12:
            return get_text("profitability.rating_very_good"), "success"
        elif ratio >= 0.08:
            return get_text("profitability.rating_good"), "info"
        elif ratio >= 0.05:
            return get_text("profitability.rating_acceptable"), "warning"
        else:
            return get_text("profitability.rating_poor"), "error"


def _get_margin_rating(margin):
    """Helper function to get rating for profit margins"""
    if margin is None:
        return "N/A", "info"

    if margin >= 0.20:
        return get_text("profitability.rating_excellent"), "success"
    elif margin >= 0.15:
        return get_text("profitability.rating_very_good"), "success"
    elif margin >= 0.10:
        return get_text("profitability.rating_good"), "info"
    elif margin >= 0.05:
        return get_text("profitability.rating_acceptable"), "warning"
    else:
        return get_text("profitability.rating_poor"), "error"


def show_profitability_analysis():
    """Profitability Analysis Interface with global ticker support"""
    st.header(f"💰 {get_text('profitability.title')}")
    st.write(get_text("profitability.description"))

    persist_data = st.session_state.persist.get("PROFITABILITY", {})

    if "global_ticker" not in st.session_state:
        st.session_state.global_ticker = st.session_state.persist.get(
            "global_ticker", "MSFT"
        )

    use_individual_ticker = st.checkbox(
        get_text("common.use_individual_ticker"),
        value=persist_data.get("use_individual_ticker", False),
        key="profit_use_individual",
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        if use_individual_ticker:
            ticker = st.text_input(
                get_text("common.ticker_symbol"),
                value=persist_data.get("ticker", ""),
                key="profit_ticker",
            ).upper()
        else:
            ticker = st.text_input(
                get_text("common.ticker_symbol") + " 🌍",
                value=st.session_state.global_ticker,
                key="profit_ticker_global",
                help=get_text("common.global_ticker_help"),
            ).upper()
            if ticker != st.session_state.global_ticker:
                st.session_state.global_ticker = ticker
                st.session_state.persist["global_ticker"] = ticker
                save_persistence_data()

    with col2:
        multi_year = st.checkbox(
            get_text("common.multi_year_checkbox"),
            value=persist_data.get("multi_year", True),
            key="profit_multi_year",
        )

    if multi_year:
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.number_input(
                get_text("common.from_year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("start_year", 2020)),
                key="profit_start_year",
            )
        with col2:
            end_year = st.number_input(
                get_text("common.to_year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("end_year", 2024)),
                key="profit_end_year",
            )
    else:
        year = st.number_input(
            get_text("common.year"),
            min_value=1990,
            max_value=2030,
            value=int(persist_data.get("year", 2024)),
            key="profit_year",
        )

    if st.button(get_text("profitability.run_analysis"), key="profit_run"):
        if not ticker:
            st.error(get_text("common.please_enter_ticker"))
        else:
            with st.spinner(get_text("profitability.calculating").format(ticker)):
                try:
                    if multi_year:
                        persist_data = {
                            "ticker": ticker if use_individual_ticker else "",
                            "use_individual_ticker": use_individual_ticker,
                            "multi_year": True,
                            "start_year": str(start_year),
                            "end_year": str(end_year),
                        }
                        st.session_state.persist.setdefault("PROFITABILITY", {}).update(
                            persist_data
                        )
                        save_persistence_data()

                        results = profitability_logic.calculate_profitability_metrics_multi_year(
                            ticker, start_year, end_year
                        )

                        if results:
                            st.success(
                                get_text("profitability.analysis_completed").format(
                                    ticker
                                )
                            )

                            table_data = []
                            for result in results:
                                roe = result.get("roe", None)
                                roa = result.get("roa", None)
                                roic = result.get("roic", None)
                                gross_margin = result.get("gross_margin", None)
                                operating_margin = result.get("operating_margin", None)
                                net_margin = result.get("net_margin", None)
                                asset_turnover = result.get("asset_turnover", None)

                                ratios = []
                                if roe is not None:
                                    ratios.append(min(roe / 0.15, 1.5))
                                if roa is not None:
                                    ratios.append(min(roa / 0.07, 1.5))
                                if net_margin is not None:
                                    ratios.append(min(net_margin / 0.15, 1.5))

                                if ratios:
                                    avg_score = sum(ratios) / len(ratios)
                                    if avg_score >= 1.2:
                                        rating = get_text(
                                            "profitability.rating_excellent"
                                        )
                                    elif avg_score >= 1.0:
                                        rating = get_text(
                                            "profitability.rating_very_good"
                                        )
                                    elif avg_score >= 0.7:
                                        rating = get_text("profitability.rating_good")
                                    elif avg_score >= 0.4:
                                        rating = get_text(
                                            "profitability.rating_acceptable"
                                        )
                                    else:
                                        rating = get_text("profitability.rating_poor")
                                else:
                                    rating = "N/A"

                                table_data.append(
                                    {
                                        get_text("common.year"): result.get("year"),
                                        get_text(
                                            "profitability.roe"
                                        ): f"{roe * 100:.1f}%"
                                        if roe is not None
                                        else "N/A",
                                        get_text(
                                            "profitability.roa"
                                        ): f"{roa * 100:.1f}%"
                                        if roa is not None
                                        else "N/A",
                                        get_text(
                                            "profitability.roic"
                                        ): f"{roic * 100:.1f}%"
                                        if roic is not None
                                        else "N/A",
                                        get_text(
                                            "profitability.gross_margin"
                                        ): f"{gross_margin * 100:.1f}%"
                                        if gross_margin is not None
                                        else "N/A",
                                        get_text(
                                            "profitability.operating_margin"
                                        ): f"{operating_margin * 100:.1f}%"
                                        if operating_margin is not None
                                        else "N/A",
                                        get_text(
                                            "profitability.net_margin"
                                        ): f"{net_margin * 100:.1f}%"
                                        if net_margin is not None
                                        else "N/A",
                                        get_text(
                                            "profitability.asset_turnover"
                                        ): f"{asset_turnover:.2f}x"
                                        if asset_turnover is not None
                                        else "N/A",
                                        get_text("profitability.rating"): rating,
                                    }
                                )

                            st.dataframe(
                                table_data, use_container_width=True, hide_index=True
                            )

                            st.info(
                                f"💡 {get_text('profitability.multi_year_info').format(start_year, end_year)}"
                            )

                        else:
                            st.warning(get_text("common.no_valid_data"))

                    else:
                        persist_data = {
                            "ticker": ticker if use_individual_ticker else "",
                            "use_individual_ticker": use_individual_ticker,
                            "multi_year": False,
                            "year": str(year),
                        }
                        st.session_state.persist.setdefault("PROFITABILITY", {}).update(
                            persist_data
                        )
                        save_persistence_data()

                        result = profitability_logic.calculate_profitability_metrics_from_ticker(
                            ticker, year
                        )

                        if result:
                            st.success(
                                get_text("profitability.analysis_completed").format(
                                    ticker
                                )
                            )

                            st.subheader(
                                f"📊 {get_text('profitability.return_ratios_section')}"
                            )
                            col1, col2, col3 = st.columns(3)

                            roe = result.get("roe", None)
                            roa = result.get("roa", None)
                            roic = result.get("roic", None)

                            with col1:
                                st.metric(
                                    get_text("profitability.roe"),
                                    f"{roe * 100:.2f}%" if roe is not None else "N/A",
                                )
                                rating, status = _get_return_rating(roe, "roe")
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
                                    get_text("profitability.roa"),
                                    f"{roa * 100:.2f}%" if roa is not None else "N/A",
                                )
                                rating, status = _get_return_rating(roa, "roa")
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
                                    get_text("profitability.roic"),
                                    f"{roic * 100:.2f}%" if roic is not None else "N/A",
                                )
                                rating, status = _get_return_rating(roic, "roic")
                                if status == "success":
                                    st.success(f"🟢 {rating}")
                                elif status == "info":
                                    st.info(f"🟡 {rating}")
                                elif status == "warning":
                                    st.warning(f"🟡 {rating}")
                                elif status == "error":
                                    st.error(f"🔴 {rating}")

                            st.markdown("---")

                            st.subheader(
                                f"📈 {get_text('profitability.profit_margins_section')}"
                            )
                            col1, col2, col3 = st.columns(3)

                            gross_margin = result.get("gross_margin", None)
                            operating_margin = result.get("operating_margin", None)
                            net_margin = result.get("net_margin", None)

                            with col1:
                                st.metric(
                                    get_text("profitability.gross_margin"),
                                    f"{gross_margin * 100:.2f}%"
                                    if gross_margin is not None
                                    else "N/A",
                                )
                                rating, status = _get_margin_rating(gross_margin)
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
                                    get_text("profitability.operating_margin"),
                                    f"{operating_margin * 100:.2f}%"
                                    if operating_margin is not None
                                    else "N/A",
                                )
                                rating, status = _get_margin_rating(operating_margin)
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
                                    get_text("profitability.net_margin"),
                                    f"{net_margin * 100:.2f}%"
                                    if net_margin is not None
                                    else "N/A",
                                )
                                rating, status = _get_margin_rating(net_margin)
                                if status == "success":
                                    st.success(f"🟢 {rating}")
                                elif status == "info":
                                    st.info(f"🟡 {rating}")
                                elif status == "warning":
                                    st.warning(f"🟡 {rating}")
                                elif status == "error":
                                    st.error(f"🔴 {rating}")

                            st.markdown("---")

                            st.subheader(
                                f"⚡ {get_text('profitability.efficiency_section')}"
                            )
                            asset_turnover = result.get("asset_turnover", None)

                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.metric(
                                    get_text("profitability.asset_turnover"),
                                    f"{asset_turnover:.2f}x"
                                    if asset_turnover is not None
                                    else "N/A",
                                )

                            with st.expander(
                                f"📊 {get_text('profitability.detailed_values')}"
                            ):
                                col1, col2 = st.columns(2)

                                revenue = result.get("revenue", 0)
                                net_income = result.get("net_income", 0)
                                total_assets = result.get("total_assets", 0)
                                shareholders_equity = result.get(
                                    "shareholders_equity", 0
                                )

                                with col1:
                                    st.metric(
                                        get_text("profitability.revenue"),
                                        f"${revenue / 1_000_000:,.2f}M",
                                    )
                                    st.metric(
                                        get_text("profitability.total_assets"),
                                        f"${total_assets / 1_000_000:,.2f}M",
                                    )

                                with col2:
                                    st.metric(
                                        get_text("profitability.net_income"),
                                        f"${net_income / 1_000_000:,.2f}M",
                                    )
                                    st.metric(
                                        get_text("profitability.shareholders_equity"),
                                        f"${shareholders_equity / 1_000_000:,.2f}M",
                                    )

                            st.info(f"💡 {get_text('profitability.info_explanation')}")

                            with st.expander(
                                f"📊 {get_text('profitability.threshold_info')}"
                            ):
                                st.write(
                                    get_text("profitability.threshold_explanation")
                                )

                                st.write(f"**{get_text('profitability.roe')}:**")
                                st.write(
                                    f"- ≥ 20%: {get_text('profitability.rating_excellent')}"
                                )
                                st.write(
                                    f"- 15-20%: {get_text('profitability.rating_very_good')}"
                                )
                                st.write(
                                    f"- 10-15%: {get_text('profitability.rating_good')}"
                                )
                                st.write(
                                    f"- 5-10%: {get_text('profitability.rating_acceptable')}"
                                )
                                st.write(
                                    f"- < 5%: {get_text('profitability.rating_poor')}"
                                )

                                st.write(f"\n**{get_text('profitability.roa')}:**")
                                st.write(
                                    f"- ≥ 10%: {get_text('profitability.rating_excellent')}"
                                )
                                st.write(
                                    f"- 7-10%: {get_text('profitability.rating_very_good')}"
                                )
                                st.write(
                                    f"- 5-7%: {get_text('profitability.rating_good')}"
                                )
                                st.write(
                                    f"- 3-5%: {get_text('profitability.rating_acceptable')}"
                                )
                                st.write(
                                    f"- < 3%: {get_text('profitability.rating_poor')}"
                                )

                                st.write(f"\n**{get_text('profitability.roic')}:**")
                                st.write(
                                    f"- ≥ 15%: {get_text('profitability.rating_excellent')}"
                                )
                                st.write(
                                    f"- 12-15%: {get_text('profitability.rating_very_good')}"
                                )
                                st.write(
                                    f"- 8-12%: {get_text('profitability.rating_good')}"
                                )
                                st.write(
                                    f"- 5-8%: {get_text('profitability.rating_acceptable')}"
                                )
                                st.write(
                                    f"- < 5%: {get_text('profitability.rating_poor')}"
                                )

                        else:
                            st.warning(get_text("common.no_valid_data"))

                except Exception as e:
                    st.error(get_text("profitability.analysis_failed").format(str(e)))
