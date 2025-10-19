import json
import os
import streamlit as st

# Basis-Pfad: backend/config/user_config/ (wird mit den Modulen geladen)
BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "backend",
    "config",
    "user_config",
)

# Admin Defaults aus frontend/config/
ADMIN_PERSISTENCE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "frontend",
    "config",
    "admin_persistence.json",
)
ADMIN_PREFERENCES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "frontend",
    "config",
    "admin_preferences.json",
)


def _ensure_directories():
    """Stelle sicher, dass das user_config Verzeichnis existiert"""
    os.makedirs(BASE_DIR, exist_ok=True)


def _get_username():
    """Hole den aktuellen Benutzernamen aus session_state"""
    return st.session_state.get("username", "admin")


def _sanitize_filename(username):
    """Bereinige Username für Dateinamen"""
    # Entferne ungültige Zeichen
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in username)


# ==================== PERSISTENCE (Modul-Einstellungen) ====================


def load_user_persistence():
    """
    Lädt benutzerspezifische Persistence-Daten.
    Falls nicht vorhanden, lade Admin-Defaults aus frontend/config/.
    """
    _ensure_directories()
    username = _sanitize_filename(_get_username())
    user_file = os.path.join(BASE_DIR, f"{username}_persistence.json")

    try:
        if os.path.exists(user_file):
            with open(user_file, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # Lade Admin-Defaults aus frontend/config/
            if os.path.exists(ADMIN_PERSISTENCE_PATH):
                with open(ADMIN_PERSISTENCE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
    except Exception as e:
        print(f"Error loading user persistence: {e}")
        return {}


def save_user_persistence(data):
    """Speichert benutzerspezifische Persistence-Daten"""
    _ensure_directories()
    username = _sanitize_filename(_get_username())
    user_file = os.path.join(BASE_DIR, f"{username}_persistence.json")

    try:
        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving user persistence: {e}")
        return False


# ==================== PREFERENCES (UI-Einstellungen) ====================


def load_user_language():
    """
    Lädt die benutzerspezifische Spracheinstellung.
    Falls nicht vorhanden, lade aus Admin-Preferences oder Default 'en'.
    """
    _ensure_directories()
    username = _sanitize_filename(_get_username())
    user_file = os.path.join(BASE_DIR, f"{username}_preferences.json")

    try:
        # Versuche benutzerspezifische Datei
        if os.path.exists(user_file):
            with open(user_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("language", "en")

        # Fallback: Admin-Preferences aus frontend/config/
        if os.path.exists(ADMIN_PREFERENCES_PATH):
            with open(ADMIN_PREFERENCES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("language", "en")

        return "en"
    except Exception as e:
        print(f"Error loading user language: {e}")
        return "en"


def save_user_language(language_code):
    """Speichert die benutzerspezifische Spracheinstellung"""
    _ensure_directories()
    username = _sanitize_filename(_get_username())
    user_file = os.path.join(BASE_DIR, f"{username}_preferences.json")

    try:
        # Lade existierende Preferences oder erstelle neue
        data = {}
        if os.path.exists(user_file):
            with open(user_file, "r", encoding="utf-8") as f:
                data = json.load(f)

        # Update language
        data["language"] = language_code

        # Speichere zurück
        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving user language: {e}")
        return False


# ==================== UTILITY FUNCTIONS ====================


def get_user_config_info():
    """
    Gibt Informationen über die User-Config-Struktur zurück.
    Nützlich für Debugging oder Admin-Panels.
    """
    _ensure_directories()
    username = _sanitize_filename(_get_username())

    persistence_file = os.path.join(BASE_DIR, f"{username}_persistence.json")
    preferences_file = os.path.join(BASE_DIR, f"{username}_preferences.json")

    return {
        "username": _get_username(),
        "sanitized_username": username,
        "base_dir": BASE_DIR,
        "persistence_file": persistence_file,
        "preferences_file": preferences_file,
        "persistence_exists": os.path.exists(persistence_file),
        "preferences_exists": os.path.exists(preferences_file),
        "admin_persistence_path": ADMIN_PERSISTENCE_PATH,
        "admin_preferences_path": ADMIN_PREFERENCES_PATH,
    }


def reset_user_config():
    """
    Setzt die User-Config auf Admin-Defaults zurück.
    Nützlich für "Reset to Defaults" Funktion.
    """
    username = _sanitize_filename(_get_username())
    persistence_file = os.path.join(BASE_DIR, f"{username}_persistence.json")
    preferences_file = os.path.join(BASE_DIR, f"{username}_preferences.json")

    try:
        # Lösche User-Dateien
        if os.path.exists(persistence_file):
            os.remove(persistence_file)
        if os.path.exists(preferences_file):
            os.remove(preferences_file)
        return True
    except Exception as e:
        print(f"Error resetting user config: {e}")
        return False


def list_all_users():
    """
    Listet alle User auf, die Config-Dateien haben.
    Nützlich für Admin-Panels.
    """
    _ensure_directories()
    users = set()

    try:
        for filename in os.listdir(BASE_DIR):
            if filename.endswith("_persistence.json") or filename.endswith(
                "_preferences.json"
            ):
                # Entferne Suffix um Username zu bekommen
                username = filename.replace("_persistence.json", "").replace(
                    "_preferences.json", ""
                )
                users.add(username)
        return sorted(list(users))
    except Exception as e:
        print(f"Error listing users: {e}")
        return []
