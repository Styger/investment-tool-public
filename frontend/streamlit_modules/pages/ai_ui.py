import streamlit as st
from ..config import get_text, save_persistence_data
import backend.valuekit_ai.core.valuekit_integration as valuekit_ai
import backend.valuekit_ai.config.analysis_config as analysis_config
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

    # Initialize CAGR state for live growth_rate field disabling
    if "ai_cagr_enabled" not in st.session_state:
        st.session_state.ai_cagr_enabled = persist_data.get("run_cagr", True)

    # Checkbox for individual ticker
    use_individual_ticker = st.checkbox(
        get_text("common.use_individual_ticker"),
        value=persist_data.get("use_individual_ticker", False),
        key="ai_use_individual",
    )

    # Main inputs
    col1, col2 = st.columns([3, 1])

    with col1:
        if use_individual_ticker:
            # Individual ticker for this module
            ticker = st.text_input(
                get_text("common.ticker_symbol"),
                value=persist_data.get("ticker", ""),
                key="ai_ticker",
            ).upper()
        else:
            # Global ticker - editable and synchronized
            ticker = st.text_input(
                get_text("common.ticker_symbol") + " 🌍",
                value=st.session_state.global_ticker,
                key="ai_ticker_global",
                help=get_text("common.global_ticker_help"),
            ).upper()
            # Update global ticker when changed
            if ticker != st.session_state.global_ticker:
                st.session_state.global_ticker = ticker
                st.session_state.persist["global_ticker"] = ticker
                save_persistence_data()

    with col2:
        year = st.number_input(
            get_text("ai.base_year"),
            min_value=2010,
            max_value=2030,
            value=int(persist_data.get("year", 2024)),
            key="ai_year",
        )

    st.markdown("---")

    # ===================================================================
    # 3-COLUMN LAYOUT: General | Quantitative | Qualitative
    # ===================================================================
    col_general, col_quant, col_qual = st.columns(3)

    # ───────────────────────────────────────────────────────────────────
    # COLUMN 1: GENERAL SETTINGS
    # ───────────────────────────────────────────────────────────────────
    with col_general:
        st.subheader(f"⚙️ {get_text('ai.general_settings')}")

        # Growth rate - disabled when CAGR is active
        growth_rate = st.number_input(
            get_text("ai.growth_rate_manual"),
            min_value=0.0,
            max_value=50.0,
            value=float(persist_data.get("growth_rate", 0.0)),
            step=1.0,
            help=get_text("ai.growth_rate_help"),
            key="ai_growth",
            disabled=st.session_state.ai_cagr_enabled,  # Live disable
        )

        # Info caption when disabled
        if st.session_state.ai_cagr_enabled:
            st.caption("⚙️ " + get_text("ai.growth_rate_auto_info"))

        # Margin of safety
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

        # Discount rate
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

        # Load SEC data - recommended for best moat results
        load_sec = st.checkbox(
            get_text("ai.load_sec_data"),
            value=persist_data.get("load_sec", True),
            key="ai_load_sec",
            help=get_text("ai.load_sec_help"),
        )

    # ───────────────────────────────────────────────────────────────────
    # COLUMN 2: QUANTITATIVE ANALYSIS
    # ───────────────────────────────────────────────────────────────────
    with col_quant:
        st.subheader(f"📊 {get_text('ai.quantitative_analysis')}")

        # MOS calculation
        run_mos = st.checkbox(
            get_text("ai.run_mos"),
            value=persist_data.get("run_mos", True),
            key="ai_toggle_mos",
        )

        # CAGR calculation - controls growth_rate field in column 1
        run_cagr = st.checkbox(
            get_text("ai.run_cagr"),
            value=st.session_state.ai_cagr_enabled,
            key="ai_toggle_cagr",
            on_change=lambda: setattr(
                st.session_state, "ai_cagr_enabled", st.session_state.ai_toggle_cagr
            ),
        )

        # Profitability analysis (ROE, ROA, ROIC, Margins)
        run_profitability = st.checkbox(
            get_text("ai.run_profitability"),
            value=persist_data.get("run_profitability", False),
            key="ai_toggle_profitability",
        )

    # ───────────────────────────────────────────────────────────────────
    # COLUMN 3: QUALITATIVE ANALYSIS (MOATS)
    # ───────────────────────────────────────────────────────────────────
    with col_qual:
        st.subheader(f"🏰 {get_text('ai.qualitative_analysis')}")

        # Master toggle for all moat analysis
        run_moat_analysis = st.checkbox(
            get_text("ai.run_moat_analysis"),
            value=persist_data.get("run_moat_analysis", True),
            key="ai_master_moats",
        )

        if run_moat_analysis:
            # Individual moat checkboxes - vertically stacked
            run_brand = st.checkbox(
                get_text("ai.moat_brand"),
                value=persist_data.get("run_brand", True),
                key="ai_moat_brand",
            )

            run_switching = st.checkbox(
                get_text("ai.moat_switching"),
                value=persist_data.get("run_switching", True),
                key="ai_moat_switching",
            )

            run_network = st.checkbox(
                get_text("ai.moat_network"),
                value=persist_data.get("run_network", True),
                key="ai_moat_network",
            )

            run_cost = st.checkbox(
                get_text("ai.moat_cost"),
                value=persist_data.get("run_cost", True),
                key="ai_moat_cost",
            )

            run_scale = st.checkbox(
                get_text("ai.moat_scale"),
                value=persist_data.get("run_scale", True),
                key="ai_moat_scale",
            )

            st.markdown("---")

            # Red flags detection
            run_red_flags = st.checkbox(
                get_text("ai.run_red_flags"),
                value=persist_data.get("run_red_flags", True),
                key="ai_toggle_flags",
            )
        else:
            # Defaults when moat analysis is disabled
            run_brand = run_switching = run_network = run_cost = run_scale = False
            run_red_flags = False

    st.markdown("---")

    # ===================================================================
    # RUN ANALYSIS BUTTON
    # ===================================================================
    if st.button(
        get_text("ai.run_analysis"),
        key="ai_run",
        type="primary",
        use_container_width=True,
    ):
        if not ticker:
            st.error(get_text("common.please_enter_ticker"))
        else:
            # Build config manually with all settings
            config = analysis_config.AnalysisConfig()

            # Quantitative settings
            config.run_mos = run_mos
            config.run_cagr = run_cagr
            config.run_profitability = run_profitability

            # Qualitative settings
            config.run_moat_analysis = run_moat_analysis
            config.run_brand_power = run_brand
            config.run_switching_costs = run_switching
            config.run_network_effects = run_network
            config.run_cost_advantages = run_cost
            config.run_efficient_scale = run_scale
            config.run_red_flags = run_red_flags

            # General settings
            config.load_sec_data = load_sec
            config.margin_of_safety = mos
            config.discount_rate = discount_rate
            config.auto_estimate_growth = growth_rate == 0

            # Save all settings to persistence
            persist_data_update = {
                "ticker": ticker if use_individual_ticker else "",
                "use_individual_ticker": use_individual_ticker,
                "year": str(year),
                "growth_rate": str(growth_rate),
                "mos": str(mos * 100),
                "discount_rate": str(discount_rate * 100),
                "load_sec": load_sec,
                "run_mos": run_mos,
                "run_cagr": run_cagr,
                "run_profitability": run_profitability,
                "run_moat_analysis": run_moat_analysis,
                "run_brand": run_brand,
                "run_switching": run_switching,
                "run_network": run_network,
                "run_cost": run_cost,
                "run_scale": run_scale,
                "run_red_flags": run_red_flags,
            }
            st.session_state.persist.setdefault("AI", {}).update(persist_data_update)
            save_persistence_data()

            # Run analysis with progress indicator
            with st.spinner(get_text("ai.analyzing").format(ticker)):
                try:
                    # Initialize analyzer
                    analyzer = valuekit_ai.ValueKitAnalyzer()

                    # Capture stdout output
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

                    # Display ONLY raw output in a big code block
                    st.subheader(f"📋 {get_text('ai.analysis_results')}")
                    st.code(output.getvalue(), language=None)

                except Exception as e:
                    st.error(get_text("ai.analysis_failed").format(str(e)))
                    import traceback

                    with st.expander(get_text("ai.error_details")):
                        st.code(traceback.format_exc())
