import sys
from pathlib import Path

# Füge das Projektverzeichnis zum Python Path hinzu
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import streamlit as st
from frontend.streamlit_modules.auth import simple_auth, show_logout
from frontend.streamlit_modules.config import (
    load_app_config,
    get_text,
    save_persistence_data,
)
from frontend.streamlit_modules.pages import (
    cagr,
    mos,
    pbt,
    tencap,
    dcf,
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

    USE_AUTH = True  # Set to False to disable authentication

    if USE_AUTH:
        if not simple_auth():
            return
        show_logout()

    load_app_config()

    # Sidebar navigation
    st.sidebar.title(f"📈 {get_text('window_title')}")

    analysis_modes = {
        f"💡 {get_text('info_help_title')}": info.show_info,
        f"📈 {get_text('cagr_title')}": cagr.show_cagr_analysis,
        f"🛡️ {get_text('mos_title')}": mos.show_mos_analysis,
        f"⏰ {get_text('pbt_title')}": pbt.show_pbt_analysis,
        f"🔟 {get_text('ten_cap_title')}": tencap.show_tencap_analysis,
        f"💰 {get_text('dcf_fmp_title')}": dcf.show_dcf_analysis,
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

    # Run selected analysis
    analysis_modes[selected_mode]()

    if selected_mode != get_text("settings_title"):
        save_persistence_data()


if __name__ == "__main__":
    main()
