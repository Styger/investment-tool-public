import streamlit as st
from streamlit_modules.auth import simple_auth, show_logout
from streamlit_modules.config import load_app_config, get_text, save_persistence_data
from streamlit_modules.pages import cagr, mos, pbt, tencap, dcf_lite, settings

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
        get_text("cagr_title"): cagr.show_cagr_analysis,
        get_text("mos_title"): mos.show_mos_analysis,
        get_text("pbt_title"): pbt.show_pbt_analysis,
        get_text("ten_cap_title"): tencap.show_tencap_analysis,
        get_text("dcf_lite_title"): dcf_lite.show_dcf_lite_analysis,
        get_text("settings_title"): settings.show_settings_page,
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
