import streamlit as st
from ..config import get_text, change_language
import backend.utils.config_load as config_load
from backend.utils.user_preferences import save_user_persistence


def show_settings_page():
    """Settings Interface - Nur benutzerspezifische Einstellungen"""
    st.header(f"⚙️ {get_text('settings.title')}")
    st.write(get_text("settings.description"))

    st.divider()

    # Language Section
    st.subheader(get_text("settings.language_settings"))

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
        get_text("settings.select_language"),
        options=list(language_options.keys()),
        index=list(language_options.keys()).index(current_display)
        if current_display in language_options
        else 0,
        key="language_selector",
    )

    if st.button(get_text("settings.change_language"), key="change_language"):
        new_lang_code = language_options[selected_lang]

        try:
            success = change_language(new_lang_code)

            if success:
                st.success(get_text("settings.language_changed"))
                st.rerun()
            else:
                st.error(get_text("settings.failed_save_language"))

        except Exception as e:
            st.error(get_text("settings.error_changing_language") + f": {str(e)}")

    st.divider()

    # Configuration Information
    st.subheader(get_text("settings.configuration_information"))

    col1, col2 = st.columns(2)

    with col1:
        st.info(f"**{get_text('settings.current_language')}:**")
        st.write(f"{current_display} ({current_lang})")

        if st.session_state.get("authenticated", False):
            username = st.session_state.get("username", "unknown")
            st.info(f"**{get_text('settings.user_specific_files')}:**")
            st.code(f"{username}_preferences.json")
            st.code(f"{username}_persistence.json")
        else:
            st.info(
                f"**{get_text('settings.status')}:** {get_text('settings.not_logged_in')}"
            )

        try:
            config_path = config_load.get_config_path()
            st.info(
                f"**{get_text('settings.config_file_location')} ({get_text('settings.central')}):**"
            )
            st.code(config_path)
        except Exception:
            st.info(get_text("settings.config_file_location_not_available"))

    with col2:
        st.info(f"**{get_text('settings.persistence_data')}:**")
        persist_data = st.session_state.get("persist", {})
        if persist_data:
            for mode, data in persist_data.items():
                st.write(
                    f"**{mode}:** {len(data)} {get_text('settings.saved_settings')}"
                )
        else:
            st.write(get_text("settings.no_saved_settings"))

        if st.button(
            get_text("settings.clear_all_saved_settings"), key="clear_settings"
        ):
            st.session_state.persist = {}
            try:
                success = save_user_persistence({})
                if success:
                    st.success(get_text("settings.all_saved_settings_cleared"))
                    st.rerun()
                else:
                    st.error(get_text("settings.error_clearing_settings"))
            except Exception as e:
                st.error(get_text("settings.error_clearing_settings") + f": {str(e)}")

    # Debug-Info (optional)
    if st.checkbox(get_text("settings.show_debug_info")):
        st.subheader(get_text("settings.debug_info"))
        st.json(
            {
                "authenticated": st.session_state.get("authenticated", False),
                "username": st.session_state.get("username", None),
                "current_language": current_lang,
                "persist_keys": list(persist_data.keys()) if persist_data else [],
            }
        )
