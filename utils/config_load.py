import json
import sys
from tkinter import messagebox
from pathlib import Path
import streamlit as st


def _resource_path(relative_path: str) -> Path:
    """Return absolute Path to an embedded resource (works in dev and PyInstaller)."""
    try:
        base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    except AttributeError:
        base_path = Path(__file__).resolve().parent.parent
    return base_path / relative_path


def get_config_path() -> str:
    return str(_resource_path("config.json"))


def get_language_path() -> str:
    return str(_resource_path("language.json"))


def load_config():
    try:
        # Load config from file first
        cfg_path = _resource_path("config.json")
        with open(cfg_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Override API Key from Streamlit secrets if available
        try:
            if hasattr(st, "secrets") and "FMP_API_KEY" in st.secrets:
                config["FMP_API_KEY"] = st.secrets["FMP_API_KEY"]
        except:
            pass  # Ignore secrets errors during development

        return config
    except Exception:
        return {}


def _save_config(new_config):
    try:
        cfg_path = _resource_path("config.json")
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(new_config, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False


def load_language():
    with open(_resource_path("language.json"), "r", encoding="utf-8") as f:
        all_languages = json.load(f)

    config = load_config()
    current_language = config.get("LANGUAGE", "de")
    language = all_languages.get(current_language, all_languages["de"])
    return language, current_language, all_languages


def save_new_key(entry_widget, language):
    new_key = entry_widget.get().strip()
    if not new_key:
        messagebox.showerror(language["error_title"], language["api_key_empty"])
        return

    config = load_config()
    config["FMP_API_KEY"] = new_key
    if _save_config(config):
        messagebox.showinfo(language["success_title"], language["api_key_saved"])
    else:
        messagebox.showerror(language["error_title"], language["api_key_not_saved"])


def on_language_change(
    selected_language,
    mode_label,
    switch_mode_fn,
    content_frame,
    global_state,
):
    selected = selected_language.get()
    config = load_config()
    config["LANGUAGE"] = selected

    if _save_config(config):
        global_state["current_language"] = selected
        global_state["language"] = global_state["all_languages"][selected]
        switch_mode_fn("Settings")


# utils/config_load.py


def save_persist_mode(mode_name, data, global_state=None):
    """
    Speichert persistente Eingabedaten für einen bestimmten GUI-Modus in config.json.

    :param mode_name: Name des Modus, z. B. "CAGR", "MOS", "TenCap"
    :param data: Dictionary mit den zu speichernden Eingaben
    :param global_state: Optional – wird aktualisiert, falls übergeben
    """
    # Bestehende Konfig laden
    config = load_config()
    config.setdefault("persist", {})

    # Kopie von data verwenden, um spätere unbeabsichtigte Änderungen zu verhindern
    config["persist"][mode_name] = dict(data)

    # Optional auch global_state updaten
    if global_state is not None:
        global_state.setdefault("persist", {})
        global_state["persist"][mode_name] = dict(data)

    # Speichern
    _save_config(config)
