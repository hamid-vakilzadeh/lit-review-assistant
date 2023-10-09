from tabs import new_interface, sidebar
from utils.session_state_vars import ensure_session_state_vars
import streamlit as st
import json
import pyrebase

# ensure the session state variables are created
ensure_session_state_vars()

pyrebaseConfig = json.loads(st.secrets["pyrebaseConfig"])

firebase = pyrebase.initialize_app(pyrebaseConfig)
auth = firebase.auth()

if __name__ == '__main__':
    if 'user' not in st.session_state:
        with st.form(key='login'):
            email = st.text_input(label='Enter your email')
            password = st.text_input(label='Enter your password', type='password')
            submit_button = st.form_submit_button(
                label='Submit',
            )

        if submit_button:
            try:
                user = auth.sign_in_with_email_and_password(
                    email=email,
                    password=password
                )
                st.session_state.user = user
                st.rerun()
            except Exception as e:
                error = e
                if "EMAIL_NOT_FOUND" in str(error):
                    st.error('Email not found')
                elif "INVALID_PASSWORD" in str(error):
                    st.error('Invalid password')
                elif "INVALID_EMAIL" in str(error):
                    st.error('Invalid email')
                else:
                    st.error(error)
                st.stop()

    else:

        new_interface.new_interface()
