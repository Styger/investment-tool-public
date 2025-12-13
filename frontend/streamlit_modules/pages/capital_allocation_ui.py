import streamlit as st
from ..config import get_text, save_persistence_data
import backend.logic.capital_allocation as capital_allocation_logic


def show_capital_allocation_analysis():
    """Capital Allocation Analysis Interface with global ticker support"""
    st.header(f"💵 {get_text('capital_allocation.title')}")
    st.write(get_text("capital_allocation.description"))

    persist_data = st.session_state.persist.get("CAPITAL_ALLOCATION", {})

    if "global_ticker" not in st.session_state:
        st.session_state.global_ticker = st.session_state.persist.get(
            "global_ticker", "MSFT"
        )

    use_individual_ticker = st.checkbox(
        get_text("common.use_individual_ticker"),
        value=persist_data.get("use_individual_ticker", False),
        key="cap_alloc_use_individual",
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        if use_individual_ticker:
            ticker = st.text_input(
                get_text("common.ticker_symbol"),
                value=persist_data.get("ticker", ""),
                key="cap_alloc_ticker",
            ).upper()
        else:
            ticker = st.text_input(
                get_text("common.ticker_symbol") + " 🌍",
                value=st.session_state.global_ticker,
                key="cap_alloc_ticker_global",
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
            key="cap_alloc_multi_year",
        )

    if multi_year:
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.number_input(
                get_text("common.from_year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("start_year", 2020)),
                key="cap_alloc_start_year",
            )
        with col2:
            end_year = st.number_input(
                get_text("common.to_year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("end_year", 2024)),
                key="cap_alloc_end_year",
            )
    else:
        year = st.number_input(
            get_text("common.year"),
            min_value=1990,
            max_value=2030,
            value=int(persist_data.get("year", 2024)),
            key="cap_alloc_year",
        )

    if st.button(get_text("capital_allocation.run_analysis"), key="cap_alloc_run"):
        if not ticker:
            st.error(get_text("common.please_enter_ticker"))
        else:
            with st.spinner(get_text("capital_allocation.calculating").format(ticker)):
                try:
                    if multi_year:
                        persist_data = {
                            "ticker": ticker if use_individual_ticker else "",
                            "use_individual_ticker": use_individual_ticker,
                            "multi_year": True,
                            "start_year": str(start_year),
                            "end_year": str(end_year),
                        }
                        st.session_state.persist.setdefault(
                            "CAPITAL_ALLOCATION", {}
                        ).update(persist_data)
                        save_persistence_data()

                        results = capital_allocation_logic.calculate_capital_allocation_multi_year(
                            ticker, start_year, end_year
                        )

                        if results:
                            st.success(
                                get_text("capital_allocation.completed").format(ticker)
                            )

                            table_data = []
                            for result in results:
                                fcf = result.get("fcf", 0)

                                dividends_paid = result.get("dividends_paid", 0)
                                dividends_pct = result.get("dividends_pct", None)
                                dividends_per_share = result.get(
                                    "dividends_per_share", None
                                )

                                stock_buybacks = result.get("stock_buybacks", 0)
                                buybacks_pct = result.get("buybacks_pct", None)
                                buybacks_per_share = result.get(
                                    "buybacks_per_share", None
                                )

                                debt_repayment = result.get("debt_repayment", 0)
                                debt_repayment_pct = result.get(
                                    "debt_repayment_pct", None
                                )
                                debt_repayment_pct_of_total = result.get(
                                    "debt_repayment_pct_of_total", None
                                )

                                capex = result.get("capex", 0)
                                capex_pct = result.get("capex_pct", None)

                                acquisitions = result.get("acquisitions", 0)
                                acquisitions_pct = result.get("acquisitions_pct", None)

                                cash_increase = result.get("cash_increase", 0)
                                cash_increase_pct = result.get(
                                    "cash_increase_pct", None
                                )

                                div_str = (
                                    f"${dividends_paid / 1_000_000:,.0f}M ({dividends_pct:.1f}%)"
                                    if dividends_pct is not None
                                    else f"${dividends_paid / 1_000_000:,.0f}M"
                                )
                                if dividends_per_share is not None:
                                    div_str += f" [${dividends_per_share:.2f}/sh]"

                                buy_str = (
                                    f"${stock_buybacks / 1_000_000:,.0f}M ({buybacks_pct:.1f}%)"
                                    if buybacks_pct is not None
                                    else f"${stock_buybacks / 1_000_000:,.0f}M"
                                )
                                if buybacks_per_share is not None:
                                    buy_str += f" [${buybacks_per_share:.2f}/sh]"

                                debt_str = (
                                    f"${debt_repayment / 1_000_000:,.0f}M ({debt_repayment_pct:.1f}%)"
                                    if debt_repayment_pct is not None
                                    else f"${debt_repayment / 1_000_000:,.0f}M"
                                )
                                if debt_repayment_pct_of_total is not None:
                                    debt_str += (
                                        f" [{debt_repayment_pct_of_total:.1f}% debt]"
                                    )

                                capex_str = (
                                    f"${capex / 1_000_000:,.0f}M ({capex_pct:.1f}%)"
                                    if capex_pct is not None
                                    else f"${capex / 1_000_000:,.0f}M"
                                )

                                ma_str = (
                                    f"${acquisitions / 1_000_000:,.0f}M ({acquisitions_pct:.1f}%)"
                                    if acquisitions_pct is not None
                                    else f"${acquisitions / 1_000_000:,.0f}M"
                                )

                                cash_str = (
                                    f"${cash_increase / 1_000_000:,.0f}M ({cash_increase_pct:.1f}%)"
                                    if cash_increase_pct is not None
                                    else f"${cash_increase / 1_000_000:,.0f}M"
                                )

                                table_data.append(
                                    {
                                        get_text("common.year"): result.get("year"),
                                        "FCF": f"${fcf / 1_000_000:,.0f}M",
                                        get_text(
                                            "capital_allocation.dividends"
                                        ): div_str,
                                        get_text(
                                            "capital_allocation.buybacks"
                                        ): buy_str,
                                        get_text(
                                            "capital_allocation.debt_repayment"
                                        ): debt_str,
                                        "Capex": capex_str,
                                        "M&A": ma_str,
                                        get_text(
                                            "capital_allocation.cash_increase"
                                        ): cash_str,
                                    }
                                )

                            st.subheader(
                                f"📊 {get_text('capital_allocation.over_time')}"
                            )
                            st.dataframe(
                                table_data,
                                use_container_width=True,
                                hide_index=True,
                            )

                            st.info(f"💡 {get_text('capital_allocation.info')}")

                        else:
                            st.warning(get_text("common.no_valid_data"))

                    else:
                        persist_data = {
                            "ticker": ticker if use_individual_ticker else "",
                            "use_individual_ticker": use_individual_ticker,
                            "multi_year": False,
                            "year": str(year),
                        }
                        st.session_state.persist.setdefault(
                            "CAPITAL_ALLOCATION", {}
                        ).update(persist_data)
                        save_persistence_data()

                        result = capital_allocation_logic.calculate_capital_allocation_from_ticker(
                            ticker, year
                        )

                        if result:
                            st.success(
                                get_text("capital_allocation.completed").format(ticker)
                            )

                            col1, col2, col3 = st.columns(3)

                            fcf = result.get("fcf", 0)
                            shares_outstanding = result.get("shares_outstanding", 0)
                            total_debt = result.get("total_debt", 0)

                            with col1:
                                st.metric(
                                    get_text("capital_allocation.free_cash_flow"),
                                    f"${fcf / 1_000_000:,.2f}M",
                                )
                            with col2:
                                st.metric(
                                    get_text("capital_allocation.shares_outstanding"),
                                    f"{shares_outstanding / 1_000_000:,.2f}M",
                                )
                            with col3:
                                st.metric(
                                    get_text("capital_allocation.total_debt"),
                                    f"${total_debt / 1_000_000:,.2f}M",
                                )

                            st.markdown("---")

                            st.subheader(
                                f"📊 {get_text('capital_allocation.breakdown')}"
                            )

                            dividends_paid = result.get("dividends_paid", 0)
                            dividends_pct = result.get("dividends_pct", None)
                            dividends_per_share = result.get(
                                "dividends_per_share", None
                            )

                            stock_buybacks = result.get("stock_buybacks", 0)
                            buybacks_pct = result.get("buybacks_pct", None)
                            buybacks_per_share = result.get("buybacks_per_share", None)

                            debt_repayment = result.get("debt_repayment", 0)
                            debt_repayment_pct = result.get("debt_repayment_pct", None)
                            debt_repayment_pct_of_total = result.get(
                                "debt_repayment_pct_of_total", None
                            )

                            capex = result.get("capex", 0)
                            capex_pct = result.get("capex_pct", None)

                            acquisitions = result.get("acquisitions", 0)
                            acquisitions_pct = result.get("acquisitions_pct", None)

                            cash_increase = result.get("cash_increase", 0)
                            cash_increase_pct = result.get("cash_increase_pct", None)

                            other = result.get("other", 0)
                            other_pct = result.get("other_pct", None)

                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.metric(
                                    get_text("capital_allocation.dividends"),
                                    f"${dividends_paid / 1_000_000:,.2f}M",
                                    delta=f"{dividends_pct:.1f}% of FCF"
                                    if dividends_pct is not None
                                    else None,
                                )
                                if dividends_per_share is not None:
                                    st.caption(
                                        f"💡 ${dividends_per_share:.2f} per share"
                                    )

                                st.metric(
                                    get_text("capital_allocation.buybacks"),
                                    f"${stock_buybacks / 1_000_000:,.2f}M",
                                    delta=f"{buybacks_pct:.1f}% of FCF"
                                    if buybacks_pct is not None
                                    else None,
                                )
                                if buybacks_per_share is not None:
                                    st.caption(
                                        f"💡 ${buybacks_per_share:.2f} per share"
                                    )

                            with col2:
                                st.metric(
                                    get_text("capital_allocation.debt_repayment"),
                                    f"${debt_repayment / 1_000_000:,.2f}M",
                                    delta=f"{debt_repayment_pct:.1f}% of FCF"
                                    if debt_repayment_pct is not None
                                    else None,
                                )
                                if debt_repayment_pct_of_total is not None:
                                    st.caption(
                                        f"💡 {debt_repayment_pct_of_total:.1f}% of total debt"
                                    )

                                st.metric(
                                    "🏗️ Capex",
                                    f"${capex / 1_000_000:,.2f}M",
                                    delta=f"{capex_pct:.1f}% of FCF"
                                    if capex_pct is not None
                                    else None,
                                )

                            with col3:
                                st.metric(
                                    "🤝 M&A",
                                    f"${acquisitions / 1_000_000:,.2f}M",
                                    delta=f"{acquisitions_pct:.1f}% of FCF"
                                    if acquisitions_pct is not None
                                    else None,
                                )
                                st.metric(
                                    get_text("capital_allocation.cash_increase"),
                                    f"${cash_increase / 1_000_000:,.2f}M",
                                    delta=f"{cash_increase_pct:.1f}% of FCF"
                                    if cash_increase_pct is not None
                                    else None,
                                )
                                st.metric(
                                    get_text("capital_allocation.other"),
                                    f"${other / 1_000_000:,.2f}M",
                                    delta=f"{other_pct:.1f}% of FCF"
                                    if other_pct is not None
                                    else None,
                                )

                            st.markdown("---")

                            st.info(f"💡 {get_text('capital_allocation.single_info')}")

                            with st.expander(
                                f"📖 {get_text('capital_allocation.explanation')}"
                            ):
                                st.write(
                                    f"**{get_text('capital_allocation.dividends')}:** {get_text('capital_allocation.dividends_explanation')}"
                                )
                                st.write(
                                    f"**{get_text('capital_allocation.buybacks')}:** {get_text('capital_allocation.buybacks_explanation')}"
                                )
                                st.write(
                                    f"**{get_text('capital_allocation.debt_repayment')}:** {get_text('capital_allocation.debt_explanation')}"
                                )
                                st.write(
                                    f"**Capex:** {get_text('capital_allocation.capex_explanation')}"
                                )
                                st.write(
                                    f"**M&A:** {get_text('capital_allocation.ma_explanation')}"
                                )
                                st.write(
                                    f"**{get_text('capital_allocation.cash_increase')}:** {get_text('capital_allocation.cash_increase_explanation')}"
                                )
                                st.write(
                                    f"**{get_text('capital_allocation.other')}:** {get_text('capital_allocation.other_explanation')}"
                                )

                        else:
                            st.warning(get_text("common.no_valid_data"))

                except Exception as e:
                    st.error(get_text("capital_allocation.failed").format(str(e)))
