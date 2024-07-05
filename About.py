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
    st.Page(about, title='Home', default=True, url_path='About.py'),
    st.Page("pages/1_AIRA App.py", title='AIRA Application'),
    st.Page("pages/2_Profile.py", title="Your Account"),
    st.Page("pages/3_Feedback.py", title="Feedback"),
    st.Page("pages/4_logout.py"),

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
            st.page_link(
                st.Page("About.py"),
                label="Home",
                icon=":material/home:",
                use_container_width=True,
            )

        with login_col:
            st.page_link(
                st.Page("pages/1_AIRA App.py"),
                label="**AIRA**",
                icon=":material/support_agent:",
                use_container_width=True,
            )

    else:
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.page_link(
                st.Page("About.py"),
                label="Home",
                icon=":material/home:",
                use_container_width=True,
            )

        with col2:
            st.page_link(
                st.Page("pages/1_AIRA App.py"),
                label="**AIRA**",
                icon=":material/support_agent:",
                use_container_width=True,
            )
        with col3:
            st.page_link(
                st.Page("pages/3_Feedback.py"),
                label="Feedback",
                icon=":material/feedback:",
                use_container_width=True,
            )
        with col4:
            st.page_link(
                st.Page("pages/2_Profile.py"),
                label="Your Account",
                icon=":material/account_box:",
                use_container_width=True,
            )
        with col5:
            st.page_link(
                st.Page("pages/4_logout.py"),
                label="Logout",
                icon=":material/logout:",
                use_container_width=True,
            )

    pg = st.navigation(my_pages,
                       position='hidden'
                       )
    pg.run()
