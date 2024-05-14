import streamlit as st
from utils.funcs import review_action_buttons
from time import time
from utils.firestore_db import new_user_request


def show_login():
    with st.form(key='login', clear_on_submit=False):
        email = st.text_input(label='Enter your email')
        password = st.text_input(label='Enter your password', type='password')
        submit_button = st.form_submit_button(
            label='Submit',
        )

    if submit_button:
        try:
            user = st.session_state.auth.sign_in_with_email_and_password(
                email=email,
                password=password
            )
            st.session_state.user = user
            st.session_state.session_start_time = time()
            st.rerun()
        except Exception as e:
            error = e
            if "EMAIL_NOT_FOUND" in str(error):
                st.error('Email not found')
            elif "INVALID_PASSWORD" in str(error):
                st.error('Invalid password')
            elif "INVALID_EMAIL" in str(error):
                st.error('Invalid email')
            elif "INVALID_LOGIN_CREDENTIALS" in str(error):
                st.error('Invalid login credentials')
            elif "MISSING_PASSWORD" in str(error):
                st.error('Please enter your password')
            else:
                st.error(error)
            # st.stop()


def show_reset_password():
    with st.form(key='reset_password', clear_on_submit=True):
        email = st.text_input(label='Enter your email')
        submit_button = st.form_submit_button(
            label='Submit',
        )

    if submit_button:
        try:
            st.session_state.auth.send_password_reset_email(email)
            st.success('If the email is a valid username, a password reset email will be sent to the provided address.')
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


def request_access():
    with st.form(key='request_access', clear_on_submit=True):
        email = st.text_input(label='Enter your email')
        submit_button = st.form_submit_button(
            label='Submit',
        )

    if submit_button:
        if '@' in email and '.' in email:
            new_user_request(username=email, _db=st.session_state.db)
            st.success('Your request has been submitted. You will receive an email when your account is ready.')

        else:
            st.error('Invalid email address.')


def login_and_reset_password():
    login, reset, request = st.tabs(['Login', 'Reset Password', 'Request Access'])
    with login:
        show_login()
    with reset:
        show_reset_password()
    with request:
        request_access()


def show_logout():
    st.button(
        label="Logout",
        type="primary",
        use_container_width=True,
        key="login",
        on_click=lambda: st.session_state.clear(),
    )


def choose_model():
    # Choose the model to use for generating the response
    chosen_model = st.selectbox(
        label='Model Name',
        options=[
            'OpenAI: GPT-4o',
            'OpenAI: GPT-3.5 16K',
            'Anthropic: Claude v2.1 200K',
            'Meta: Llama v2 70B Chat',
            'Google: Gemini Pro',
                 ],
    )
    if chosen_model == 'OpenAI: GPT-3.5 16K':
        st.session_state.selected_model = 'openai/gpt-3.5-turbo-16k'
    if chosen_model == 'OpenAI: GPT-4o':
        st.session_state.selected_model = 'openai/gpt-4o'
    if chosen_model == 'Anthropic: Claude v2.1 200K':
        st.session_state.selected_model = 'anthropic/claude-2'
    if chosen_model == 'Meta: Llama v2 70B Chat':
        st.session_state.selected_model = 'meta-llama/llama-2-70b-chat'
    if chosen_model == 'Google: Gemini Pro':
        st.session_state.selected_model = 'google/gemini-pro'


def show_sidebar():
    # sidebar
    with st.sidebar:
        choose_model()
        st.header("📌 My Pinboard")
        st.markdown("You can keep track of abstract, summaries, and reviews "
                    "that you pin while you are reviewing the literature. "
                    )
        st.radio(
            label="Show Pinned:",
            options=[
                f"Abstracts: {len(st.session_state.pinned_articles)}",
                f"PDF pieces: {len(st.session_state.pinned_pdfs)}",
            ],
            key="show_pinned",
            horizontal=True,
        )
        # st.subheader(f"Selected pieces for review: {len(st.session_state.review_pieces)}")
        disable_status = True
        if st.session_state.pinned_articles or st.session_state.pinned_pdfs:
            disable_status = False
        st.button(
            label="Clear all pinned",
            key="clear_pinned",
            on_click=lambda: [
                st.session_state.pop("pinned_articles", None),
                st.session_state.pop("pinned_pdfs", None),
                st.session_state.pop("review_pieces", None),
            ],
            type="secondary",
            disabled=disable_status,
            use_container_width=True,
        )
        if st.session_state.show_pinned == f"Abstracts: {len(st.session_state.pinned_articles)}":
            st.markdown("Articles that you have found in the **Articles** tab.")
            for article in st.session_state.pinned_articles:
                st.markdown(f"**{article['title']}**")
                review_action_buttons(article, st.session_state.pinned_articles)
                st.markdown(f"{article['doi'].strip()}" ,)
                st.markdown(f"{article['text']}")
                st.markdown("---")
        elif st.session_state.show_pinned == f"PDF pieces: {len(st.session_state.pinned_pdfs)}":
            st.markdown("Summaries that you have created in the **MyPDF** tab.")
            for piece in st.session_state.pinned_pdfs:
                st.markdown(f"**{piece['citation'][0].strip()}**")
                review_action_buttons(piece, st.session_state.pinned_pdfs)
                st.markdown(f"{piece['prompt']}")
                st.markdown(f"{piece['text']}")
                st.markdown("---")
