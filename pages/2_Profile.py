from tabs import profile, sidebar
from utils.session_state_vars import ensure_session_state_vars
import streamlit as st

# ensure the session state variables are created
ensure_session_state_vars()


if __name__ == '__main__':
    if 'user' not in st.session_state:
        sidebar.login_and_reset_password()

    else:
        with st.sidebar:
            sidebar.show_logout()
        profile.profile()
