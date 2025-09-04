import streamlit as st
import pandas as pd
import io
import sys
import os
import utils.config_load as config_load
from utils.user_preferences import (
    load_user_language,
    save_user_language,
    load_user_persistence,
    save_user_persistence,
)


def load_app_config():
    # Zuerst lokale Streamlit secrets prüfen
    secrets_path = ".streamlit/secrets.toml"
    if os.path.exists(secrets_path):
        # Streamlit lädt automatisch .streamlit/secrets.toml
        pass

    """Load configuration and initialize session state"""
    if "config_loaded" not in st.session_state:
        try:
            # Zentrale Konfiguration laden (API Key etc.)
            cfg = config_load.load_config()

            # Benutzerspezifische Sprache laden
            user_language_code = load_user_language()

            # Language-Dateien laden
            language, current_language, all_languages = config_load.load_language()

            # Override mit benutzerspezifischer Sprache
            if user_language_code in all_languages:
                language = all_languages[user_language_code]
                current_language = user_language_code

            st.session_state.language = language
            st.session_state.current_language = current_language
            st.session_state.all_languages = all_languages

            # Benutzerspezifische Persistence laden (falls angemeldet)
            if st.session_state.get("authenticated", False):
                st.session_state.persist = load_user_persistence()
            else:
                st.session_state.persist = {}

            st.session_state.config = cfg
            st.session_state.config_loaded = True
        except Exception as e:
            st.error(f"Error loading configuration: {e}")
            # Fallback configuration
            st.session_state.language = {
                "window_title": "Stock Analysis Tool",
                "error_title": "Error",
                "success_title": "Success",
                "api_key_empty": "API Key cannot be empty",
                "api_key_saved": "API Key saved successfully",
                "api_key_not_saved": "Failed to save API Key",
            }
            st.session_state.current_language = "en"
            st.session_state.all_languages = {"en": st.session_state.language}
            st.session_state.persist = {}
            st.session_state.config = {}


def reload_user_config():
    """Lädt benutzerspezifische Einstellungen nach Login/Logout neu"""
    try:
        # Benutzerspezifische Sprache laden
        user_language_code = load_user_language()
        all_languages = st.session_state.get("all_languages", {})

        # Sprache aktualisieren
        if user_language_code in all_languages:
            st.session_state.language = all_languages[user_language_code]
            st.session_state.current_language = user_language_code

        # Benutzerspezifische Persistence laden
        if st.session_state.get("authenticated", False):
            st.session_state.persist = load_user_persistence()
        else:
            st.session_state.persist = {}

    except Exception as e:
        print(f"Error reloading user config: {e}")


def get_text(key, fallback=None):
    """Get localized text from language JSON"""
    language_data = st.session_state.get("language", {})
    if key in language_data:
        return language_data[key]

    # Fallback to English if key not found in current language
    all_languages = st.session_state.get("all_languages", {})
    if "en" in all_languages and key in all_languages["en"]:
        return all_languages["en"][key]

    # Final fallback
    return fallback if fallback else key


def save_persistence_data():
    """Save current persistence data benutzerspezifisch"""
    try:
        if st.session_state.get("authenticated", False):
            persist_data = st.session_state.get("persist", {})
            save_user_persistence(persist_data)
    except Exception:
        pass  # Fail silently


def change_language(new_language):
    """Ändert die Sprache und speichert sie benutzerspezifisch"""
    try:
        # Speichere neue Sprache benutzerspezifisch
        if save_user_language(new_language):
            # Aktualisiere Session State
            all_languages = st.session_state.get("all_languages", {})
            if new_language in all_languages:
                st.session_state.language = all_languages[new_language]
                st.session_state.current_language = new_language
                return True
    except Exception as e:
        print(f"Error changing language: {e}")
    return False


def capture_output(func, *args, **kwargs):
    """Capture printed output from analysis functions"""
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output

    try:
        result = func(*args, **kwargs)
        output = redirected_output.getvalue()
        return result, output
    finally:
        sys.stdout = old_stdout
