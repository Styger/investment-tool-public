import sys
from pathlib import Path


import streamlit as st
import frontend.streamlit_modules.auth
import frontend.streamlit_modules.config as config
import frontend.streamlit_modules.pages as pages

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
        if not frontend.streamlit_modules.auth.simple_auth():
            return
        frontend.streamlit_modules.auth.show_logout()

    config.load_app_config()

    # Sidebar navigation
    st.sidebar.title(f"📈 {config.get_text('window_title')}")

    analysis_modes = {
        f"💡 {config.get_text('info_help_title')}": pages.info.show_info,
        f"📈 {config.get_text('cagr_title')}": pages.cagr.show_cagr_analysis,
        f"🛡️ {config.get_text('mos_title')}": pages.mos.show_mos_analysis,
        f"⏰ {config.get_text('pbt_title')}": pages.pbt.show_pbt_analysis,
        f"🔟 {config.get_text('ten_cap_title')}": pages.tencap.show_tencap_analysis,
        f"💰 {config.get_text('dcf_fmp_title')}": pages.dcf.show_dcf_analysis,
        f"⚙️ {config.get_text('settings_title')}": pages.settings.show_settings_page,
    }

    selected_mode = st.sidebar.selectbox(
        config.get_text("select_analysis_mode"),
        list(analysis_modes.keys()),
        key="analysis_mode",
    )

    st.sidebar.markdown(f"**{config.get_text('current_mode')}:** {selected_mode}")
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### {config.get_text('about')}")
    st.sidebar.info(config.get_text("about_description"))

    # Run selected analysis
    analysis_modes[selected_mode]()

    if selected_mode != config.get_text("settings_title"):
        config.save_persistence_data()


if __name__ == "__main__":
    main()
