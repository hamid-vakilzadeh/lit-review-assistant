from tabs import new_interface, sidebar
from utils.session_state_vars import ensure_session_state_vars
import streamlit as st
from tabs.css import css_code
# ensure the session state variables are created
ensure_session_state_vars()

# run the css
css_code()

if __name__ == '__main__':
    if 'user' not in st.session_state:
        sidebar.login_and_reset_password()

    else:
        with st.sidebar:
            sidebar.show_logout()

        new_interface.new_interface()
