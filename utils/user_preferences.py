import json
import os
import streamlit as st
from pathlib import Path
import sys


def _resource_path(relative_path: str) -> Path:
    """Return absolute Path to an embedded resource."""
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        base_path = Path(__file__).resolve().parent.parent
    return base_path / relative_path


def get_user_filename(file_type):
    """Erstellt benutzerspezifische Dateinamen"""
    username = st.session_state.get("username", "default")
    return str(_resource_path(f"{username}_{file_type}.json"))


def load_user_language():
    """Lädt benutzerspezifische Spracheinstellung"""
    pref_file = get_user_filename("preferences")

    try:
        if os.path.exists(pref_file):
            with open(pref_file, "r", encoding="utf-8") as f:
                prefs = json.load(f)
                return prefs.get("language", "de")
    except:
        pass
    return "de"  # Standard


def save_user_language(language):
    """Speichert benutzerspezifische Spracheinstellung"""
    pref_file = get_user_filename("preferences")

    # Lade existierende Präferenzen
    prefs = {}
    if os.path.exists(pref_file):
        try:
            with open(pref_file, "r", encoding="utf-8") as f:
                prefs = json.load(f)
        except:
            pass

    # Aktualisiere Sprache
    prefs["language"] = language

    # Speichere
    try:
        with open(pref_file, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2)
        return True
    except:
        return False


def load_user_persistence():
    """Lädt benutzerspezifische letzte Eingaben"""
    persist_file = get_user_filename("persistence")

    try:
        if os.path.exists(persist_file):
            with open(persist_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {}


def save_user_persistence(data):
    """Speichert benutzerspezifische letzte Eingaben"""
    persist_file = get_user_filename("persistence")

    try:
        with open(persist_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except:
        return False
