import streamlit as st
from frontend.streamlit_modules.auth import simple_auth, show_logout
from frontend.streamlit_modules.config import (
    load_app_config,
    get_text,
    initialize_global_ticker,
)
from frontend.streamlit_modules.pages import (
    cagr,
    mos,
    pbt,
    tencap,
    dcf,
    debt,
    profitability,
    capital_allocation,  # NEU
    settings,
    info,
)

# Page configuration
st.set_page_config(
    page_title="Stock Analysis Tool",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main application with simple authentication"""

    USE_AUTH = True

    if USE_AUTH:
        if not simple_auth():
            return
        show_logout()

    load_app_config()

    st.sidebar.title(f"📈 {get_text('window_title')}")

    analysis_modes = {
        f"💡 {get_text('info_help_title')}": info.show_info,
        f"📈 {get_text('cagr_title')}": cagr.show_cagr_analysis,
        f"🛡️ {get_text('mos_title')}": mos.show_mos_analysis,
        f"⏰ {get_text('pbt_title')}": pbt.show_pbt_analysis,
        f"🔟 {get_text('ten_cap_title')}": tencap.show_tencap_analysis,
        f"💸 {get_text('dcf_fmp_title')}": dcf.show_dcf_analysis,
        f"💳 {get_text('debt_title')}": debt.show_debt_analysis,
        f"💰 {get_text('profitability_title')}": profitability.show_profitability_analysis,
        f"💵 {get_text('capital_allocation_title')}": capital_allocation.show_capital_allocation_analysis,  # NEU
        # f"💎 {get_text('quality_title')}": quality.show_quality_analysis,  # SPÄTER!
        f"⚙️ {get_text('settings_title')}": settings.show_settings_page,
    }

    selected_mode = st.sidebar.selectbox(
        get_text("select_analysis_mode"),
        list(analysis_modes.keys()),
        key="analysis_mode",
    )

    st.sidebar.markdown(f"**{get_text('current_mode')}:** {selected_mode}")
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### {get_text('about')}")
    st.sidebar.info(get_text("about_description"))

    analysis_modes[selected_mode]()
    initialize_global_ticker()


if __name__ == "__main__":
    main()
