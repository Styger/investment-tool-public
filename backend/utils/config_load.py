import json
import sys
import streamlit as st
from pathlib import Path

from frontend.streamlit_modules import config


def _resource_path(relative_path: str) -> Path:
    """Return absolute Path to an embedded resource."""
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        base_path = (
            Path(__file__).resolve().parent.parent.parent
        )  # ✅ GEÄNDERT: Ein parent mehr (zu Projekt-Root)
    return base_path / relative_path


def get_config_path() -> str:
    return str(_resource_path("frontend/config/config.json"))  # ✅ GEÄNDERT


def get_language_path() -> str:
    return str(_resource_path("frontend/config/language.json"))  # ✅ GEÄNDERT


def load_config():
    config = {}

    if hasattr(st, "secrets") and "FMP_API_KEY" in st.secrets:
        config["FMP_API_KEY"] = st.secrets["FMP_API_KEY"]

    return config


def _save_config(new_config):
    try:
        cfg_path = _resource_path("frontend/config/config.json")  # ✅ GEÄNDERT
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(new_config, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False


def load_language():
    with open(
        _resource_path("frontend/config/language.json"),
        "r",
        encoding="utf-8",  # ✅ GEÄNDERT
    ) as f:
        all_languages = json.load(f)

    config = load_config()
    current_language = config.get("LANGUAGE", "de")
    language = all_languages.get(current_language, all_languages["de"])
    return language, current_language, all_languages


def save_persist_mode(mode_name, data, global_state=None):
    """Speichert persistente Eingabedaten für einen bestimmten GUI-Modus in config.json."""
    config = load_config()
    config.setdefault("persist", {})
    config["persist"][mode_name] = dict(data)

    if global_state is not None:
        global_state.setdefault("persist", {})
        global_state["persist"][mode_name] = dict(data)

    _save_config(config)
