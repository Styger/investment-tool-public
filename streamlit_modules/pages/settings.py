import streamlit as st
from ..config import get_text
import utils.config_load as config_load


def show_settings_page():
    """Settings Interface"""
    st.header(f"⚙️ {get_text('settings_title')}")
    st.write(get_text("settings_description"))

    # API Key Section
    st.subheader(get_text("api_configuration"))

    current_config = st.session_state.get("config", {})
    current_key = current_config.get("FMP_API_KEY", "")

    col1, col2 = st.columns([3, 1])

    with col1:
        api_key = st.text_input(
            get_text("financial_modeling_prep_api_key"),
            value=current_key,
            type="password",
            help=get_text("api_key_help"),
            key="api_key_input",
        )

    with col2:
        show_key = st.checkbox(get_text("show_key"), key="show_api_key")
        if show_key and api_key:
            st.text_input(
                get_text("current_key"),
                value=api_key,
                disabled=True,
                key="visible_api_key",
            )

    if st.button(get_text("save_button"), key="save_api_key"):
        if not api_key.strip():
            st.error(get_text("api_key_empty"))
        else:
            try:
                # Update session state config
                if "config" not in st.session_state:
                    st.session_state.config = {}
                st.session_state.config["FMP_API_KEY"] = api_key.strip()

                # Save to file
                success = config_load._save_config(st.session_state.config)
                if success:
                    st.success(get_text("api_key_saved"))
                else:
                    st.error(get_text("api_key_not_saved"))
            except Exception as e:
                st.error(get_text("error_saving_api_key") + f": {str(e)}")

    st.divider()

    # Language Section
    st.subheader(get_text("language_settings"))

    current_lang = st.session_state.get("current_language", "en")
    all_languages = st.session_state.get("all_languages", {})

    # Create language options from available languages
    language_options = {}
    for lang_code, lang_data in all_languages.items():
        if lang_code == "en":
            language_options["English"] = lang_code
        elif lang_code == "de":
            language_options["Deutsch"] = lang_code
        else:
            language_options[lang_code.upper()] = lang_code

    if not language_options:
        language_options = {"English": "en", "Deutsch": "de"}

    # Find current language display name
    current_display = "English"
    for display_name, code in language_options.items():
        if code == current_lang:
            current_display = display_name
            break

    selected_lang = st.selectbox(
        get_text("select_language"),
        options=list(language_options.keys()),
        index=list(language_options.keys()).index(current_display)
        if current_display in language_options
        else 0,
        key="language_selector",
    )

    if st.button(get_text("change_language"), key="change_language"):
        new_lang_code = language_options[selected_lang]

        try:
            # Update config
            if "config" not in st.session_state:
                st.session_state.config = {}
            st.session_state.config["LANGUAGE"] = new_lang_code

            # Save to file
            success = config_load._save_config(st.session_state.config)

            if success:
                # Update session state
                st.session_state.current_language = new_lang_code
                if new_lang_code in all_languages:
                    st.session_state.language = all_languages[new_lang_code]

                st.success(get_text("language_changed"))
                st.rerun()
            else:
                st.error(get_text("failed_save_language"))

        except Exception as e:
            st.error(get_text("error_changing_language") + f": {str(e)}")

    st.divider()

    # Configuration Information
    st.subheader(get_text("configuration_information"))

    col1, col2 = st.columns(2)

    with col1:
        st.info(f"**{get_text('current_language')}:**")
        st.write(f"{current_display} ({current_lang})")

        try:
            config_path = config_load.get_config_path()
            st.info(f"**{get_text('config_file_location')}:**")
            st.code(config_path)
        except Exception:
            st.info(get_text("config_file_location_not_available"))

    with col2:
        st.info(f"**{get_text('persistence_data')}:**")
        persist_data = st.session_state.get("persist", {})
        if persist_data:
            for mode, data in persist_data.items():
                st.write(f"**{mode}:** {len(data)} {get_text('saved_settings')}")
        else:
            st.write(get_text("no_saved_settings"))

        # Option to clear persistence data
        if st.button(get_text("clear_all_saved_settings"), key="clear_settings"):
            st.session_state.persist = {}
            try:
                if "config" not in st.session_state:
                    st.session_state.config = {}
                st.session_state.config["persist"] = {}
                config_load._save_config(st.session_state.config)
                st.success(get_text("all_saved_settings_cleared"))
                st.rerun()
            except Exception as e:
                st.error(get_text("error_clearing_settings") + f": {str(e)}")
