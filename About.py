import streamlit as st
from tabs import sidebar, updates
from utils.session_state_vars import ensure_session_state_vars
from tabs.css import css_code
from tabs.dialogs import search_dialog, advanced_search_dialog, pdf_dialog, temporary_dialog

# ensure the session state variables are created
ensure_session_state_vars()


def about():
    # display the header and general settings
    with st.container():
        # The header
        st.header("AIRA: AI Research Assistant")

        # The description
        st.markdown(
            """
            This app is designed to assist researchers in finding and organizing literature.
            """
        )

    # display the instructions
    with st.container():
        st.video(
            data="https://www.youtube.com/watch?v=-93awViey4o",
            autoplay=False
        )

    with st.container(height=500):
        updates.updates()


my_pages = [
    st.Page(about, title='Home', default=True, url_path='About.py'),
    st.Page("the_pages/1_AIRA App.py", title='AIRA Application'),
    st.Page("the_pages/3_Feedback.py", title="Feedback"),
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

    main_menu_col, research_tools_col, other_chats_col = st.columns(3)
    
    with main_menu_col.popover("Main Menu", use_container_width=True):
        st.page_link(
            st.Page("About.py"),
            label="Home",
            icon=":material/home:",
            use_container_width=True,
        )

        st.page_link(
            st.Page("the_pages/1_AIRA App.py"),
            label="**AIRA**",
            icon=":material/support_agent:",
            use_container_width=True,
        )

        st.page_link(
            st.Page("the_pages/3_Feedback.py"),
            label="Feedback",
            icon=":material/feedback:",
            use_container_width=True,
        )

    pg = st.navigation(my_pages, position='hidden')
    
    if pg.url_path == 'AIRA_App':
        with research_tools_col.popover("Research Tools", use_container_width=True):
            if st.button("Advanced Search", use_container_width=True):
                advanced_search_dialog()

            if st.button("PDF", use_container_width=True):
                pdf_dialog()

    pg.run()
