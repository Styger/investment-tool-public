import streamlit as st
import io
import sys
import os
import backend.utils.config_load as config_load
from backend.utils.user_preferences import (
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
    """Get localized text from language JSON with dot notation support"""
    language_data = st.session_state.get("language", {})

    # Split key by dot for nested access (e.g., "mos.title")
    keys = key.split(".")
    value = language_data

    # Navigate through nested structure
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            # Key not found - try fallback to English
            all_languages = st.session_state.get("all_languages", {})
            if "en" in all_languages:
                en_value = all_languages["en"]
                for k in keys:
                    if isinstance(en_value, dict) and k in en_value:
                        en_value = en_value[k]
                    else:
                        # Not in English either - use fallback
                        return fallback if fallback else key
                return (
                    en_value
                    if isinstance(en_value, str)
                    else (fallback if fallback else key)
                )

            return fallback if fallback else key

    # Return the value if it's a string, otherwise fallback
    return value if isinstance(value, str) else (fallback if fallback else key)


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


def set_global_ticker():
    """
    Funktion zum Setzen des globalen Tickers.
    Sollte in der Sidebar oder am Anfang deiner App aufgerufen werden.
    """
    import streamlit as st

    # Initialisiere global_ticker falls nicht vorhanden
    if "global_ticker" not in st.session_state:
        st.session_state.global_ticker = ""

    # Sidebar Widget für globalen Ticker
    with st.sidebar:
        st.markdown("---")
        st.subheader("🌍 Global Settings")

        new_global_ticker = st.text_input(
            "Global Ticker",
            value=st.session_state.global_ticker,
            key="global_ticker_input",
            help="This ticker will be used across all analysis modules unless 'Individual Ticker' is selected",
        ).upper()

        # Update session state wenn sich der Wert ändert
        if new_global_ticker != st.session_state.global_ticker:
            st.session_state.global_ticker = new_global_ticker

        if st.session_state.global_ticker:
            st.success(f"Global Ticker: **{st.session_state.global_ticker}**")
        else:
            st.info("No global ticker set")

        st.markdown("---")


def initialize_global_ticker():
    """
    Initialisiert den globalen Ticker im session_state.
    Lädt ihn aus der Persistence oder setzt Default "MSFT".
    Sollte einmalig am Anfang der App aufgerufen werden.
    """
    import streamlit as st

    if "global_ticker" not in st.session_state:
        # Lade aus Persistence oder setze Default
        persist_data = st.session_state.get("persist", {})
        st.session_state.global_ticker = persist_data.get("global_ticker", "MSFT")


def initialize_global_ticker():
    """
    Initialisiert den globalen Ticker im session_state.
    Lädt ihn aus der Persistence oder setzt Default "MSFT".
    Sollte einmalig am Anfang der App aufgerufen werden.
    """
    import streamlit as st

    if "global_ticker" not in st.session_state:
        # Lade aus Persistence oder setze Default
        persist_data = st.session_state.get("persist", {})
        st.session_state.global_ticker = persist_data.get("global_ticker", "MSFT")


def save_global_ticker():
    """
    Speichert den globalen Ticker in die Persistence.
    Wird automatisch in den Modulen aufgerufen.
    """
    import streamlit as st

    if "global_ticker" in st.session_state:
        st.session_state.persist["global_ticker"] = st.session_state.global_ticker
        save_persistence_data()


def save_persistence_data():
    """Save current persistence data benutzerspezifisch in frontend/config/user_config/"""
    try:
        if st.session_state.get("authenticated", False):
            from backend.utils.user_preferences import save_user_persistence

            persist_data = st.session_state.get("persist", {})
            save_user_persistence(persist_data)
    except Exception as e:
        print(f"Error saving persistence: {e}")
        pass  # Fail silently


def get_effective_ticker(module_ticker, use_individual):
    """
    Hilfsfunktion um den effektiven Ticker zu bekommen.

    Args:
        module_ticker: Der im Modul eingegebene Ticker
        use_individual: Ob individueller Ticker verwendet werden soll

    Returns:
        Der zu verwendende Ticker (entweder global oder individuell)
    """
    import streamlit as st

    if use_individual:
        return module_ticker
    else:
        return st.session_state.get("global_ticker", "")
