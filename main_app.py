import streamlit as st
from frontend.streamlit_modules.auth import simple_auth, show_logout
from frontend.streamlit_modules.config import (
    load_app_config,
    get_text,
    initialize_global_ticker,
)
from frontend.streamlit_modules.pages import (
    cagr_ui,
    capital_allocation_ui,
    dcf_ui,
    debt_ui,
    info_ui,
    mos_ui,
    pbt_ui,
    profitability_ui,
    settings_ui,
    tencap_ui,
    ai_ui,
    backtesting_ui,
    screening_ui,
)

# Page configurationselect_analysis_mode
st.set_page_config(
    page_title="Stock Analysis Tool",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize worker on first run
if "worker_initialized" not in st.session_state:
    from backend.jobs.worker_manager import ensure_worker_running

    worker = ensure_worker_running()

    # ✅ FORCE POLLING MODE (more reliable for Streamlit)
    worker.start_worker(mode="polling")

    status = worker.get_status()

    print(f"✅ Worker initialized: {status}")
    st.session_state["worker_initialized"] = True
    st.session_state["worker_status"] = status


def main():
    """Main application with simple authentication"""

    USE_AUTH = True

    if USE_AUTH:
        if not simple_auth():
            return
        show_logout()

    load_app_config()

    st.sidebar.title(f"📈 {get_text('app.window_title')}")

    analysis_modes = {
        f"💡 {get_text('info.page_title')}": info_ui.show_info,
        f"📈 {get_text('cagr.title')}": cagr_ui.show_cagr_analysis,
        f"🛡️ {get_text('mos.title')}": mos_ui.show_mos_analysis,
        f"⏰ {get_text('pbt.title')}": pbt_ui.show_pbt_analysis,
        f"🔟 {get_text('tencap.title')}": tencap_ui.show_tencap_analysis,
        f"💸 {get_text('dcf.title')}": dcf_ui.show_dcf_analysis,
        f"💳 {get_text('debt.title')}": debt_ui.show_debt_analysis,
        f"💰 {get_text('profitability.title')}": profitability_ui.show_profitability_analysis,
        f"💵 {get_text('capital_allocation.title')}": capital_allocation_ui.show_capital_allocation_analysis,
        # f"💎 {get_text('quality_title')}": quality.show_quality_analysis,
        f"🤖 {get_text('ai.title')}": ai_ui.show_ai_analysis,
        f"⚙️ {get_text('settings.title')}": settings_ui.show_settings_page,
        f"📊 {get_text('backtesting.title')}": backtesting_ui.show_backtesting_page,
        f"🔍 {get_text('screening.title')}": screening_ui.show_screening_page,
    }

    selected_mode = st.sidebar.selectbox(
        get_text("app.select_analysis_mode"),
        list(analysis_modes.keys()),
        key="analysis_mode",
    )

    st.sidebar.markdown(f"**{get_text('app.current_mode')}:** {selected_mode}")
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### {get_text('app.about')}")
    st.sidebar.info(get_text("app.about_description"))

    analysis_modes[selected_mode]()
    initialize_global_ticker()


if __name__ == "__main__":
    main()
