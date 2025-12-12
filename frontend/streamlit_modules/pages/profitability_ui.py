import streamlit as st
from ..config import get_text, save_persistence_data
import backend.logic.profitability as profitability_logic


def _get_return_rating(ratio, metric_type):
    """Helper function to get rating for return ratios (ROE, ROA)"""
    if ratio is None:
        return "N/A", "info"

    if metric_type == "roe":
        # ROE thresholds
        if ratio >= 0.20:  # >= 20%
            return get_text("profit_rating_excellent"), "success"
        elif ratio >= 0.15:  # >= 15%
            return get_text("profit_rating_very_good"), "success"
        elif ratio >= 0.10:  # >= 10%
            return get_text("profit_rating_good"), "info"
        elif ratio >= 0.05:  # >= 5%
            return get_text("profit_rating_acceptable"), "warning"
        else:
            return get_text("profit_rating_poor"), "error"

    elif metric_type == "roa":
        # ROA thresholds
        if ratio >= 0.10:  # >= 10%
            return get_text("profit_rating_excellent"), "success"
        elif ratio >= 0.07:  # >= 7%
            return get_text("profit_rating_very_good"), "success"
        elif ratio >= 0.05:  # >= 5%
            return get_text("profit_rating_good"), "info"
        elif ratio >= 0.03:  # >= 3%
            return get_text("profit_rating_acceptable"), "warning"
        else:
            return get_text("profit_rating_poor"), "error"

    elif metric_type == "roic":
        # ROIC thresholds
        if ratio >= 0.15:  # >= 15%
            return get_text("profit_rating_excellent"), "success"
        elif ratio >= 0.12:  # >= 12%
            return get_text("profit_rating_very_good"), "success"
        elif ratio >= 0.08:  # >= 8%
            return get_text("profit_rating_good"), "info"
        elif ratio >= 0.05:  # >= 5%
            return get_text("profit_rating_acceptable"), "warning"
        else:
            return get_text("profit_rating_poor"), "error"


def _get_margin_rating(margin):
    """Helper function to get rating for profit margins"""
    if margin is None:
        return "N/A", "info"

    if margin >= 0.20:  # >= 20%
        return get_text("profit_rating_excellent"), "success"
    elif margin >= 0.15:  # >= 15%
        return get_text("profit_rating_very_good"), "success"
    elif margin >= 0.10:  # >= 10%
        return get_text("profit_rating_good"), "info"
    elif margin >= 0.05:  # >= 5%
        return get_text("profit_rating_acceptable"), "warning"
    else:
        return get_text("profit_rating_poor"), "error"


def show_profitability_analysis():
    """Profitability Analysis Interface with global ticker support"""
    st.header(f"💰 {get_text('profitability_title')}")
    st.write(get_text("profitability_description"))

    persist_data = st.session_state.persist.get("PROFITABILITY", {})

    # Initialisiere global_ticker falls nicht vorhanden - lade aus Persistence
    if "global_ticker" not in st.session_state:
        st.session_state.global_ticker = st.session_state.persist.get(
            "global_ticker", "MSFT"
        )

    # Checkbox für individuellen Ticker
    use_individual_ticker = st.checkbox(
        get_text("use_individual_ticker", "Use individual ticker"),
        value=persist_data.get("use_individual_ticker", False),
        key="profit_use_individual",
    )

    # First row: Ticker and Multi-year checkbox
    col1, col2 = st.columns([3, 1])

    with col1:
        if use_individual_ticker:
            # Individueller Ticker für dieses Modul
            ticker = st.text_input(
                get_text("ticker_symbol"),
                value=persist_data.get("ticker", ""),
                key="profit_ticker",
            ).upper()
        else:
            # Globaler Ticker - editierbar und synchronisiert
            ticker = st.text_input(
                get_text("ticker_symbol") + " 🌍",
                value=st.session_state.global_ticker,
                key="profit_ticker_global",
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
        multi_year = st.checkbox(
            get_text("multi_year_question"),
            value=persist_data.get("multi_year", True),
            key="profit_multi_year",
        )

    # Second row: Year selection (single or range)
    if multi_year:
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.number_input(
                get_text("from_year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("start_year", 2020)),
                key="profit_start_year",
            )
        with col2:
            end_year = st.number_input(
                get_text("to_year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("end_year", 2024)),
                key="profit_end_year",
            )
    else:
        year = st.number_input(
            get_text("base_year"),
            min_value=1990,
            max_value=2030,
            value=int(persist_data.get("year", 2024)),
            key="profit_year",
        )

    if st.button(get_text("run_profitability_analysis"), key="profit_run"):
        if not ticker:
            st.error(get_text("please_enter_ticker"))
        else:
            with st.spinner(get_text("calculating_profitability").format(ticker)):
                try:
                    if multi_year:
                        # Save to persistence
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

                        # Multi-year analysis
                        results = profitability_logic.calculate_profitability_metrics_multi_year(
                            ticker, start_year, end_year
                        )

                        if results:
                            st.success(
                                get_text("profitability_analysis_completed").format(
                                    ticker
                                )
                            )

                            # Create table data
                            table_data = []
                            for result in results:
                                roe = result.get("roe", None)
                                roa = result.get("roa", None)
                                roic = result.get("roic", None)
                                gross_margin = result.get("gross_margin", None)
                                operating_margin = result.get("operating_margin", None)
                                net_margin = result.get("net_margin", None)
                                asset_turnover = result.get("asset_turnover", None)

                                # Average rating based on key metrics
                                ratios = []
                                if roe is not None:
                                    ratios.append(
                                        min(roe / 0.15, 1.5)
                                    )  # Normalize to ~1.0
                                if roa is not None:
                                    ratios.append(min(roa / 0.07, 1.5))
                                if net_margin is not None:
                                    ratios.append(min(net_margin / 0.15, 1.5))

                                if ratios:
                                    avg_score = sum(ratios) / len(ratios)
                                    if avg_score >= 1.2:
                                        rating = get_text("profit_rating_excellent")
                                    elif avg_score >= 1.0:
                                        rating = get_text("profit_rating_very_good")
                                    elif avg_score >= 0.7:
                                        rating = get_text("profit_rating_good")
                                    elif avg_score >= 0.4:
                                        rating = get_text("profit_rating_acceptable")
                                    else:
                                        rating = get_text("profit_rating_poor")
                                else:
                                    rating = "N/A"

                                table_data.append(
                                    {
                                        get_text("year"): result.get("year"),
                                        get_text("roe_label"): f"{roe * 100:.1f}%"
                                        if roe is not None
                                        else "N/A",
                                        get_text("roa_label"): f"{roa * 100:.1f}%"
                                        if roa is not None
                                        else "N/A",
                                        "ROIC": f"{roic * 100:.1f}%"
                                        if roic is not None
                                        else "N/A",
                                        get_text(
                                            "gross_margin_label"
                                        ): f"{gross_margin * 100:.1f}%"
                                        if gross_margin is not None
                                        else "N/A",
                                        get_text(
                                            "operating_margin_label"
                                        ): f"{operating_margin * 100:.1f}%"
                                        if operating_margin is not None
                                        else "N/A",
                                        get_text(
                                            "net_margin_label"
                                        ): f"{net_margin * 100:.1f}%"
                                        if net_margin is not None
                                        else "N/A",
                                        get_text(
                                            "asset_turnover_label"
                                        ): f"{asset_turnover:.2f}x"
                                        if asset_turnover is not None
                                        else "N/A",
                                        get_text("profit_rating"): rating,
                                    }
                                )

                            # Display table
                            st.dataframe(table_data, use_container_width=True)

                            # Info note
                            st.info(
                                f"💡 {get_text('profit_multi_year_info').format(start_year, end_year)}"
                            )

                        else:
                            st.warning(get_text("no_valid_data"))

                    else:
                        # Save to persistence
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

                        # Single year analysis
                        result = profitability_logic.calculate_profitability_metrics_from_ticker(
                            ticker, year
                        )

                        if result:
                            st.success(
                                get_text("profitability_analysis_completed").format(
                                    ticker
                                )
                            )

                            # Section 1: Return Ratios
                            st.subheader(f"📊 {get_text('return_ratios_section')}")
                            col1, col2, col3 = st.columns(3)

                            roe = result.get("roe", None)
                            roa = result.get("roa", None)
                            roic = result.get("roic", None)

                            with col1:
                                st.metric(
                                    get_text("roe_label"),
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
                                    get_text("roa_label"),
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
                                    "ROIC",
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

                            # Section 2: Profit Margins
                            st.subheader(f"📈 {get_text('profit_margins_section')}")
                            col1, col2, col3 = st.columns(3)

                            gross_margin = result.get("gross_margin", None)
                            operating_margin = result.get("operating_margin", None)
                            net_margin = result.get("net_margin", None)

                            with col1:
                                st.metric(
                                    get_text("gross_margin_label"),
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
                                    get_text("operating_margin_label"),
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
                                    get_text("net_margin_label"),
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

                            # Section 3: Efficiency
                            st.subheader(f"⚡ {get_text('efficiency_section')}")
                            asset_turnover = result.get("asset_turnover", None)

                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.metric(
                                    get_text("asset_turnover_label"),
                                    f"{asset_turnover:.2f}x"
                                    if asset_turnover is not None
                                    else "N/A",
                                )

                            # Detailed values in expander
                            with st.expander(
                                f"📊 {get_text('profit_detailed_values')}"
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
                                        get_text("revenue"),
                                        f"${revenue / 1_000_000:,.2f}M",
                                    )
                                    st.metric(
                                        get_text("total_assets"),
                                        f"${total_assets / 1_000_000:,.2f}M",
                                    )

                                with col2:
                                    st.metric(
                                        get_text("net_income"),
                                        f"${net_income / 1_000_000:,.2f}M",
                                    )
                                    st.metric(
                                        get_text("shareholders_equity"),
                                        f"${shareholders_equity / 1_000_000:,.2f}M",
                                    )

                            # Info box with interpretation
                            st.info(f"💡 {get_text('profit_info_explanation')}")

                            # Threshold explanation in expander
                            with st.expander(f"📊 {get_text('profit_threshold_info')}"):
                                st.write(get_text("profit_threshold_explanation"))

                                st.write(f"**{get_text('roe_label')}:**")
                                st.write(
                                    f"- ≥ 20%: {get_text('profit_rating_excellent')}"
                                )
                                st.write(
                                    f"- 15-20%: {get_text('profit_rating_very_good')}"
                                )
                                st.write(f"- 10-15%: {get_text('profit_rating_good')}")
                                st.write(
                                    f"- 5-10%: {get_text('profit_rating_acceptable')}"
                                )
                                st.write(f"- < 5%: {get_text('profit_rating_poor')}")

                                st.write(f"\n**{get_text('roa_label')}:**")
                                st.write(
                                    f"- ≥ 10%: {get_text('profit_rating_excellent')}"
                                )
                                st.write(
                                    f"- 7-10%: {get_text('profit_rating_very_good')}"
                                )
                                st.write(f"- 5-7%: {get_text('profit_rating_good')}")
                                st.write(
                                    f"- 3-5%: {get_text('profit_rating_acceptable')}"
                                )
                                st.write(f"- < 3%: {get_text('profit_rating_poor')}")

                                st.write(f"\n**ROIC:**")
                                st.write(
                                    f"- ≥ 15%: {get_text('profit_rating_excellent')}"
                                )
                                st.write(
                                    f"- 12-15%: {get_text('profit_rating_very_good')}"
                                )
                                st.write(f"- 8-12%: {get_text('profit_rating_good')}")
                                st.write(
                                    f"- 5-8%: {get_text('profit_rating_acceptable')}"
                                )
                                st.write(f"- < 5%: {get_text('profit_rating_poor')}")

                        else:
                            st.warning(get_text("no_valid_data"))

                except Exception as e:
                    st.error(get_text("profitability_analysis_failed").format(str(e)))
