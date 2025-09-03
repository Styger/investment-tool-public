import streamlit as st


def load_user_credentials():
    """Load user credentials from Streamlit secrets"""
    try:
        if hasattr(st, "secrets") and "users" in st.secrets:
            return dict(st.secrets["users"])
        else:
            st.error("No user configuration found.")
            return {}
    except Exception as e:
        st.error(f"Error loading authentication: {str(e)}")
        return {}


def simple_auth():
    """Einfache Session-basierte Authentifizierung mit Streamlit Secrets"""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["username"] = None

    if not st.session_state["authenticated"]:
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

            if username in valid_users and valid_users[username] == password:
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.success("Erfolgreich angemeldet!")
                st.rerun()
            else:
                st.error("Falscher Username oder Passwort")

        return False
    return True


def show_logout():
    """Logout-Button in der Sidebar"""
    if st.session_state.get("authenticated", False):
        st.sidebar.write(
            f"Angemeldet als: **{st.session_state.get('username', 'User')}**"
        )
        if st.sidebar.button("Logout", key="logout_button"):
            st.session_state["authenticated"] = False
            st.session_state["username"] = None
            st.rerun()
