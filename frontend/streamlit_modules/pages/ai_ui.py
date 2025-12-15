import streamlit as st
from ..config import get_text, save_persistence_data
import backend.valuekit_ai.valuekit_integration as valuekit_ai
import backend.valuekit_ai.analysis_config as analysis_config
from io import StringIO
import contextlib


@contextlib.contextmanager
def capture_stdout():
    """Capture stdout for displaying in Streamlit"""
    import sys

    old_stdout = sys.stdout
    sys.stdout = buffer = StringIO()
    try:
        yield buffer
    finally:
        sys.stdout = old_stdout


def show_ai_analysis():
    """AI Investment Analysis Interface with ValueKit integration"""
    st.header(f"🤖 {get_text('ai.title')}")
    st.write(get_text("ai.description"))

    persist_data = st.session_state.persist.get("AI", {})

    # Initialize global_ticker if not present
    if "global_ticker" not in st.session_state:
        st.session_state.global_ticker = st.session_state.persist.get(
            "global_ticker", "MSFT"
        )

    # Checkbox for individual ticker
    use_individual_ticker = st.checkbox(
        get_text("common.use_individual_ticker"),
        value=persist_data.get("use_individual_ticker", False),
        key="ai_use_individual",
    )

    # Main inputs in columns
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if use_individual_ticker:
            ticker = st.text_input(
                get_text("common.ticker_symbol"),
                value=persist_data.get("ticker", ""),
                key="ai_ticker",
            ).upper()
        else:
            ticker = st.text_input(
                get_text("common.ticker_symbol") + " 🌍",
                value=st.session_state.global_ticker,
                key="ai_ticker_global",
                help=get_text("common.global_ticker_help"),
            ).upper()
            if ticker != st.session_state.global_ticker:
                st.session_state.global_ticker = ticker
                st.session_state.persist["global_ticker"] = ticker
                save_persistence_data()

    with col2:
        preset = st.selectbox(
            get_text("ai.preset_label"),
            [
                get_text("ai.preset_quick"),
                get_text("ai.preset_quant_only"),
                get_text("ai.preset_qual_only"),
            ],
            index=["quick", "quant_only", "qual_only"].index(
                persist_data.get("preset", "quick")
            ),
            key="ai_preset",
        )

    with col3:
        year = st.number_input(
            get_text("ai.base_year"),
            min_value=2010,
            max_value=2030,
            value=int(persist_data.get("year", 2024)),
            key="ai_year",
        )

    # Advanced options in expander
    with st.expander(get_text("ai.advanced_options")):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            growth_rate = st.number_input(
                get_text("ai.growth_rate_manual"),
                min_value=0.0,
                max_value=50.0,
                value=float(persist_data.get("growth_rate", 0.0)),
                step=1.0,
                help=get_text("ai.growth_rate_help"),
                key="ai_growth",
            )

        with col2:
            mos = (
                st.number_input(
                    get_text("ai.margin_of_safety"),
                    min_value=0.0,
                    max_value=75.0,
                    value=float(persist_data.get("mos", 50.0)),
                    step=5.0,
                    key="ai_mos",
                )
                / 100
            )

        with col3:
            discount_rate = (
                st.number_input(
                    get_text("ai.discount_rate"),
                    min_value=1.0,
                    max_value=30.0,
                    value=float(persist_data.get("discount_rate", 15.0)),
                    step=1.0,
                    key="ai_discount",
                )
                / 100
            )

        with col4:
            load_sec = st.checkbox(
                get_text("ai.load_sec_data"),
                value=persist_data.get("load_sec", False),
                key="ai_load_sec",
            )

        # Component toggles
        st.markdown(f"**{get_text('ai.components_label')}**")
        col1, col2, col3 = st.columns(3)

        with col1:
            run_mos = st.checkbox(
                get_text("ai.run_mos"), value=True, key="ai_toggle_mos"
            )
            run_cagr = st.checkbox(
                get_text("ai.run_cagr"), value=True, key="ai_toggle_cagr"
            )

        with col2:
            run_moats = st.checkbox(
                get_text("ai.run_moats"), value=True, key="ai_toggle_moats"
            )
            run_red_flags = st.checkbox(
                get_text("ai.run_red_flags"), value=True, key="ai_toggle_flags"
            )

    # Run Analysis Button
    if st.button(get_text("ai.run_analysis"), key="ai_run", type="primary"):
        if not ticker:
            st.error(get_text("common.please_enter_ticker"))
        else:
            # Build config based on preset and toggles
            if get_text("ai.preset_quant_only") in preset:
                config = analysis_config.quantitative_only()
            elif get_text("ai.preset_qual_only") in preset:
                config = analysis_config.qualitative_only()
            else:
                config = analysis_config.quick_config()

            # Apply toggles
            config.run_mos = run_mos
            config.run_cagr = run_cagr
            config.run_moat_analysis = run_moats
            config.run_red_flags = run_red_flags
            config.load_sec_data = load_sec
            config.margin_of_safety = mos
            config.discount_rate = discount_rate

            # Save to persistence
            persist_data_update = {
                "ticker": ticker if use_individual_ticker else "",
                "use_individual_ticker": use_individual_ticker,
                "preset": ["quick", "quant_only", "qual_only"][
                    [
                        get_text("ai.preset_quick"),
                        get_text("ai.preset_quant_only"),
                        get_text("ai.preset_qual_only"),
                    ].index(preset)
                ],
                "year": str(year),
                "growth_rate": str(growth_rate),
                "mos": str(mos * 100),
                "discount_rate": str(discount_rate * 100),
                "load_sec": load_sec,
            }
            st.session_state.persist.setdefault("AI", {}).update(persist_data_update)
            save_persistence_data()

            # Run analysis with progress
            with st.spinner(get_text("ai.analyzing").format(ticker)):
                # Initialize analyzer
                analyzer = valuekit_ai.ValueKitAnalyzer()

                # Capture output
                with capture_stdout() as output:
                    result = analyzer.analyze_stock_complete(
                        ticker=ticker,
                        year=year,
                        growth_rate=growth_rate if growth_rate > 0 else None,
                        discount_rate=discount_rate,
                        margin_of_safety=mos,
                        auto_estimate_growth=(growth_rate == 0),
                        load_sec_data=load_sec,
                        config=config,
                    )

                st.success(get_text("ai.analysis_completed").format(ticker))

                # Display results in formatted sections
                _display_results(result)

                # Show raw output in expander
                with st.expander(f"📋 {get_text('ai.raw_output')}", expanded=False):
                    st.code(output.getvalue(), language=None)


def _display_results(result: dict):
    """Display formatted AI analysis results"""

    # Growth Analysis
    if result.get("growth_analysis"):
        growth = result["growth_analysis"]
        st.subheader(f"📈 {get_text('ai.growth_analysis_title')}")

        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric(
                get_text("ai.analysis_period"),
                f"{growth['start_year']}-{growth['end_year']} ({growth['period_years']}y)",
            )
            st.metric(
                get_text("ai.average_growth"),
                f"{growth['avg_growth_rate'] * 100:.2f}%",
            )

        with col2:
            metrics_data = {
                get_text("ai.book_value_cagr"): f"{growth['book_cagr']:.2f}%",
                get_text("ai.eps_cagr"): f"{growth['eps_cagr']:.2f}%",
                get_text("ai.revenue_cagr"): f"{growth['revenue_cagr']:.2f}%",
                get_text("ai.cashflow_cagr"): f"{growth['cashflow_cagr']:.2f}%",
            }
            st.table(metrics_data)

        st.markdown("---")

    # Intrinsic Value
    if result.get("intrinsic_value"):
        mos = result["intrinsic_value"]
        st.subheader(f"💰 {get_text('ai.intrinsic_value_title')}")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                get_text("common.current_stock_price"),
                f"${mos['Current Stock Price']:,.2f}",
            )

        with col2:
            st.metric(
                get_text("ai.fair_value_today"), f"${mos['Fair Value Today']:,.2f}"
            )

        with col3:
            st.metric(get_text("ai.mos_price"), f"${mos['MOS Price']:,.2f}")

        with col4:
            valuation = mos["Price vs Fair Value"]
            if "Undervalued" in valuation:
                st.success(f"📈 {valuation}")
            elif "Overvalued" in valuation:
                st.warning(f"📉 {valuation}")
            else:
                st.info(f"⚖️ {valuation}")

        st.info(
            f"**{get_text('ai.mos_recommendation')}:** {mos['Investment Recommendation']}"
        )
        st.markdown("---")

    # AI Moat Analysis
    if result.get("ai_analysis"):
        ai = result["ai_analysis"]
        moat = ai.moat_analysis

        st.subheader(f"🏰 {get_text('ai.moat_analysis_title')}")

        # Overall scores
        num_moats = len(moat.moats)
        max_possible = num_moats * 10

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                get_text("ai.overall_moat_score"),
                f"{moat.overall_score}/{max_possible}",
            )
        with col2:
            st.metric(get_text("ai.moat_strength"), moat.moat_strength)
        with col3:
            st.metric(get_text("ai.competitive_position"), moat.competitive_position)

        # Individual moat scores
        st.markdown(f"**{get_text('ai.individual_moats')}:**")

        sorted_moats = sorted(
            moat.moats.items(), key=lambda x: x[1].score, reverse=True
        )

        for key, m in sorted_moats:
            emoji = "🟢" if m.score >= 7 else ("🟡" if m.score >= 4 else "🔴")
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"{emoji} **{m.name}**")
            with col2:
                st.write(f"{m.score}/10")
            with col3:
                st.write(m.confidence)

        # Red Flags
        if moat.red_flags:
            st.warning(
                f"🚩 **{get_text('ai.red_flags_detected')} ({len(moat.red_flags)}):**"
            )
            for i, flag in enumerate(moat.red_flags, 1):
                st.write(f"{i}. {flag}")
        else:
            st.success(f"✅ {get_text('ai.no_red_flags')}")

        st.markdown("---")

        # AI Decision
        st.subheader(f"🤖 {get_text('ai.ai_decision_title')}")

        col1, col2, col3 = st.columns(3)
        with col1:
            decision = ai.decision
            if "Buy" in decision:
                st.success(f"**{get_text('ai.decision')}:** {decision}")
            elif "Hold" in decision:
                st.warning(f"**{get_text('ai.decision')}:** {decision}")
            else:
                st.error(f"**{get_text('ai.decision')}:** {decision}")

        with col2:
            st.metric(get_text("ai.confidence"), ai.confidence)

        with col3:
            st.metric(get_text("ai.overall_score"), f"{ai.overall_score}/100")

        # Score breakdown
        st.markdown(f"**{get_text('ai.score_breakdown')}:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                get_text("ai.quantitative_score"),
                f"{ai.quantitative_score}/100",
                help=get_text("ai.quantitative_weight"),
            )
        with col2:
            st.metric(
                get_text("ai.qualitative_score"),
                f"{ai.qualitative_score}/100",
                help=get_text("ai.qualitative_weight"),
            )
        with col3:
            penalty = ai.overall_score - int(
                (ai.quantitative_score * 0.6 + ai.qualitative_score * 0.4)
            )
            st.metric(get_text("ai.red_flag_penalty"), f"{penalty}")

    # Final Recommendation
    st.markdown("---")
    st.subheader(f"🎯 {get_text('ai.final_recommendation_title')}")
    st.info(result.get("final_recommendation", get_text("ai.no_recommendation")))
