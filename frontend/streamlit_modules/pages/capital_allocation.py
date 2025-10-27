import streamlit as st
from ..config import get_text, save_persistence_data
import backend.logic.capital_allocation as capital_allocation_logic


def show_capital_allocation_analysis():
    """Capital Allocation Analysis Interface with global ticker support"""
    st.header(
        f"💵 {get_text('capital_allocation_title', 'Capital Allocation Analysis')}"
    )
    st.write(
        get_text(
            "capital_allocation_description",
            "Analyze how the company uses its Free Cash Flow",
        )
    )

    persist_data = st.session_state.persist.get("CAPITAL_ALLOCATION", {})

    # Initialisiere global_ticker falls nicht vorhanden - lade aus Persistence
    if "global_ticker" not in st.session_state:
        st.session_state.global_ticker = st.session_state.persist.get(
            "global_ticker", "MSFT"
        )

    # Checkbox für individuellen Ticker
    use_individual_ticker = st.checkbox(
        get_text("use_individual_ticker", "Use individual ticker"),
        value=persist_data.get("use_individual_ticker", False),
        key="cap_alloc_use_individual",
    )

    # First row: Ticker and Multi-year checkbox
    col1, col2 = st.columns([3, 1])

    with col1:
        if use_individual_ticker:
            # Individueller Ticker für dieses Modul
            ticker = st.text_input(
                get_text("ticker_symbol"),
                value=persist_data.get("ticker", ""),
                key="cap_alloc_ticker",
            ).upper()
        else:
            # Globaler Ticker - editierbar und synchronisiert
            ticker = st.text_input(
                get_text("ticker_symbol") + " 🌍",
                value=st.session_state.global_ticker,
                key="cap_alloc_ticker_global",
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
            key="cap_alloc_multi_year",
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
                key="cap_alloc_start_year",
            )
        with col2:
            end_year = st.number_input(
                get_text("to_year"),
                min_value=1990,
                max_value=2030,
                value=int(persist_data.get("end_year", 2024)),
                key="cap_alloc_end_year",
            )
    else:
        year = st.number_input(
            get_text("base_year"),
            min_value=1990,
            max_value=2030,
            value=int(persist_data.get("year", 2024)),
            key="cap_alloc_year",
        )

    if st.button(
        get_text("run_capital_allocation_analysis", "Run Capital Allocation Analysis"),
        key="cap_alloc_run",
    ):
        if not ticker:
            st.error(get_text("please_enter_ticker"))
        else:
            with st.spinner(
                get_text(
                    "calculating_capital_allocation",
                    "Calculating capital allocation for {0}...",
                ).format(ticker)
            ):
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
                        st.session_state.persist.setdefault(
                            "CAPITAL_ALLOCATION", {}
                        ).update(persist_data)
                        save_persistence_data()

                        # Multi-year analysis
                        results = capital_allocation_logic.calculate_capital_allocation_multi_year(
                            ticker, start_year, end_year
                        )

                        if results:
                            st.success(
                                get_text(
                                    "capital_allocation_completed",
                                    "Capital allocation analysis completed for {0}",
                                ).format(ticker)
                            )

                            # Create table data
                            table_data = []
                            for result in results:
                                fcf = result.get("fcf", 0)

                                # Get values
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

                                # Format combined strings
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
                                        get_text("year"): result.get("year"),
                                        "FCF": f"${fcf / 1_000_000:,.0f}M",
                                        get_text("dividends", "Dividends"): div_str,
                                        get_text("buybacks", "Buybacks"): buy_str,
                                        get_text(
                                            "debt_repayment", "Debt Repay"
                                        ): debt_str,
                                        "Capex": capex_str,
                                        "M&A": ma_str,
                                        get_text("cash_increase", "Cash ↑"): cash_str,
                                    }
                                )

                            # Display table
                            st.subheader(
                                f"📊 {get_text('capital_allocation_over_time', 'Capital Allocation Over Time')}"
                            )
                            st.dataframe(
                                table_data,
                                use_container_width=True,
                                hide_index=True,
                            )

                            # Info box
                            st.info(
                                f"💡 {get_text('cap_alloc_info', 'The percentages show how the Free Cash Flow was allocated. Total can exceed 100% if financed from other sources.')}"
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
                        st.session_state.persist.setdefault(
                            "CAPITAL_ALLOCATION", {}
                        ).update(persist_data)
                        save_persistence_data()

                        # Single year analysis
                        result = capital_allocation_logic.calculate_capital_allocation_from_ticker(
                            ticker, year
                        )

                        if result:
                            st.success(
                                get_text(
                                    "capital_allocation_completed",
                                    "Capital allocation analysis completed for {0}",
                                ).format(ticker)
                            )

                            # Display FCF and context
                            col1, col2, col3 = st.columns(3)

                            fcf = result.get("fcf", 0)
                            shares_outstanding = result.get("shares_outstanding", 0)
                            total_debt = result.get("total_debt", 0)

                            with col1:
                                st.metric(
                                    get_text("free_cash_flow", "Free Cash Flow"),
                                    f"${fcf / 1_000_000:,.2f}M",
                                )
                            with col2:
                                st.metric(
                                    get_text(
                                        "shares_outstanding", "Shares Outstanding"
                                    ),
                                    f"{shares_outstanding / 1_000_000:,.2f}M",
                                )
                            with col3:
                                st.metric(
                                    get_text("total_debt", "Total Debt"),
                                    f"${total_debt / 1_000_000:,.2f}M",
                                )

                            st.markdown("---")

                            # Section: Capital Allocation Breakdown
                            st.subheader(
                                f"📊 {get_text('capital_allocation_breakdown', 'Capital Allocation Breakdown')}"
                            )

                            # Get values
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

                            # Display in columns
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.metric(
                                    get_text("dividends", "💵 Dividends"),
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
                                    get_text("buybacks", "🔄 Buybacks"),
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
                                    get_text("debt_repayment", "💳 Debt Repayment"),
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
                                    get_text("cash_increase", "💰 Cash Increase"),
                                    f"${cash_increase / 1_000_000:,.2f}M",
                                    delta=f"{cash_increase_pct:.1f}% of FCF"
                                    if cash_increase_pct is not None
                                    else None,
                                )
                                st.metric(
                                    get_text("other", "📦 Other"),
                                    f"${other / 1_000_000:,.2f}M",
                                    delta=f"{other_pct:.1f}% of FCF"
                                    if other_pct is not None
                                    else None,
                                )

                            st.markdown("---")

                            # Info and explanation
                            st.info(
                                f"💡 {get_text('cap_alloc_single_info', 'Shows how the company allocated its Free Cash Flow. Percentages may exceed 100% if financed from other sources.')}"
                            )

                            # Explanation expander
                            with st.expander(
                                f"📖 {get_text('cap_alloc_explanation', 'What do these categories mean?')}"
                            ):
                                st.write(
                                    f"**{get_text('dividends', 'Dividends')}:** {get_text('dividends_explanation', 'Cash paid to shareholders as dividends')}"
                                )
                                st.write(
                                    f"**{get_text('buybacks', 'Buybacks')}:** {get_text('buybacks_explanation', 'Money spent on repurchasing own shares')}"
                                )
                                st.write(
                                    f"**{get_text('debt_repayment', 'Debt Repayment')}:** {get_text('debt_explanation', 'Repayment of debt obligations')}"
                                )
                                st.write(
                                    f"**Capex:** {get_text('capex_explanation', 'Capital expenditure for maintaining and growing the business')}"
                                )
                                st.write(
                                    f"**M&A:** {get_text('ma_explanation', 'Mergers and acquisitions spending')}"
                                )
                                st.write(
                                    f"**{get_text('cash_increase', 'Cash Increase')}:** {get_text('cash_increase_explanation', 'Increase in cash and cash equivalents on the balance sheet')}"
                                )
                                st.write(
                                    f"**{get_text('other', 'Other')}:** {get_text('other_explanation', 'Other uses of cash not categorized above')}"
                                )

                        else:
                            st.warning(get_text("no_valid_data"))

                except Exception as e:
                    st.error(
                        get_text(
                            "capital_allocation_failed",
                            "Capital allocation analysis failed: {0}",
                        ).format(str(e))
                    )
