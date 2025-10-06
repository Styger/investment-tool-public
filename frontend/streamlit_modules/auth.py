import streamlit as st
from . import config


def load_user_credentials():
    """Load user credentials from Streamlit secrets"""
    if not hasattr(st, "secrets") or "users" not in st.secrets:
        return {}
    return dict(st.secrets["users"])


def load_user_credentials_eafp():
    """Load user credentials from Streamlit secrets"""
    if not hasattr(st, "secrets") or "users" not in st.secrets:
        raise Exception("No user credentials found")
    return dict(st.secrets["users"])


def load_user_credentials_3():
    """Load user credentials from Streamlit secrets"""
    if not hasattr(st, "secrets") or "users" not in st.secrets:
        st.warning("No user credentials found in secrets. Authentication disabled.")
        return
    return dict(st.secrets["users"])


def simple_auth():
    """Einfache Session-basierte Authentifizierung mit Streamlit Secrets"""

    # Debug-Output
    st.sidebar.write(
        f"🐛 Auth Status: {st.session_state.get('authenticated', 'NOT SET')}"
    )

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["username"] = None

    if st.session_state["authenticated"]:
        return True

    st.title("Investment Tool - Login")
    st.write("Bitte melden Sie sich an, um fortzufahren.")

    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username", key="login_user")
    with col2:
        password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login", key="login_button"):
        valid_users = load_user_credentials()

        if not valid_users:
            st.error("System configuration error. Please contact administrator.")
            return False
        if username not in valid_users or valid_users[username] != password:
            st.error("Falscher Username oder Passwort")
            return False

        # Setze Session State und rerun SOFORT
        st.session_state["authenticated"] = True
        st.session_state["username"] = username
        config.reload_user_config()
        st.rerun()
        # KEIN Code nach st.rerun()!

    return False


def show_logout():
    """Logout-Button in der Sidebar"""
    if not st.session_state.get("authenticated", False):  # ← FIX
        return

    st.sidebar.write(f"Angemeldet als: **{st.session_state.get('username', 'User')}**")
    if st.sidebar.button("Logout", key="logout_button"):
        st.session_state["authenticated"] = False
        st.session_state["username"] = None

        # Import und Aufruf nach dem Zurücksetzen
        from . import config

        config.reload_user_config()

        st.rerun()
