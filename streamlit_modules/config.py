import streamlit as st
import pandas as pd
import io
import sys
import utils.config_load as config_load


def load_app_config():
    """Load configuration and initialize session state"""
    if "config_loaded" not in st.session_state:
        try:
            language, current_language, all_languages = config_load.load_language()
            cfg = config_load.load_config()

            st.session_state.language = language
            st.session_state.current_language = current_language
            st.session_state.all_languages = all_languages
            st.session_state.persist = cfg.get("persist", {})
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
    """Save current persistence data to config"""
    try:
        current_config = st.session_state.get("config", {})
        current_config["persist"] = st.session_state.get("persist", {})
        config_load._save_config(current_config)
    except Exception:
        pass  # Fail silently


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
