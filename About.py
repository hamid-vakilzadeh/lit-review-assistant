import streamlit as st
from tabs import sidebar, updates
from utils.session_state_vars import ensure_session_state_vars
from tabs.css import css_code

# ensure the session state variables are created
ensure_session_state_vars()


def about():
    col_1, col_2, col_3 = st.columns([1, 2, 1])
    # display the header and general settings
    with st.container():
        # The header
        col_2.header("AIRA: AI Research Assistant")

        # The description
        col_2.markdown(
            """
            This app is designed to assist researchers in finding and organizing literature.
            """
        )

    # display the instructions
    with st.container():
        col_2.video(
            data="https://www.youtube.com/watch?v=-93awViey4o",
            autoplay=False
        )

    with col_2.container(height=500):
        updates.updates()


my_pages = [
    st.Page(about, title='About', default=True, url_path='About.py'),
    st.Page("pages/1_AIRA App.py", title='AIRA Application'),
    st.Page("pages/2_Profile.py", title="Your Account"),
    st.Page("pages/3_Feedback.py", title="Feedback"),
]

if __name__ == '__main__':

    # make page wide
    st.set_page_config(
        layout="wide",
        page_title="AI Research Assistant",
        page_icon="📚",
    )
    # run the css
    css_code()

    if 'user' not in st.session_state:
        col3, col4, about_button, login_col, col5, col6 = st.columns(6)
        with about_button:
            st.button(
                label="About",
                use_container_width=True,
                key='about_button',
                type='primary'
            )
        with login_col:
            st.button(
                label="Login or Sign Up",
                use_container_width=True,
                type='primary',
                key='login_button',
            )

        if st.session_state.login_button:
            st.switch_page("pages/1_AIRA App.py")

    else:
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.button(
                label="About",
                use_container_width=True,
                key='about_button',
                type='primary'
            )
        with col2:
            st.button(
                label="**AIRA**",
                use_container_width=True,
                key='aira_button',
                type='primary'
            )
        with col3:
            st.button(
                label="Feedback",
                use_container_width=True,
                key='feedback_button',
                type='primary'
            )
        with col4:
            st.button(
                label="Your Account",
                use_container_width=True,
                key='profile_button',
                type='primary'
            )
        with col5:
            st.button(
                label="**Logout**",
                use_container_width=True,
                key='logout_button',
                type='secondary',
                on_click=lambda: st.session_state.clear(),

            )

        if st.session_state.aira_button:
            st.switch_page("pages/1_AIRA App.py")

        if st.session_state.profile_button:
            st.switch_page("pages/2_Profile.py")

        if st.session_state.feedback_button:
            st.switch_page("pages/3_Feedback.py")

    if st.session_state.about_button:
        st.switch_page(st.Page("About.py"))

    pg = st.navigation(my_pages,
                       position='hidden'
                       )
    pg.run()