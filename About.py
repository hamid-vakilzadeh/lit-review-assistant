import streamlit as st
from tabs import sidebar, article_search, pdf_search, literature_review, updates
from utils.session_state_vars import ensure_session_state_vars

# ensure the session state variables are created
ensure_session_state_vars()

if __name__ == '__main__':
    # make page wide
    st.set_page_config(
        layout="centered",
        page_title="AI Research Assistant",
        page_icon="📚",
    )

    #if 'user' not in st.session_state:
        #sidebar.login_and_reset_password()

    # else:

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
    with st.sidebar:
        if 'user' in st.session_state:
            sidebar.show_logout()

    # display the instructions
    with st.container():
        st.video(
            data="https://www.youtube.com/watch?v=-93awViey4o"
        )
    # sidebar.show_sidebar()

    # article_search_tab, pdf_tab, literature_review_tab = st.tabs(
    #    ["**Articles**", "**My PDFs**", "**Literature Review**"]
    # )

    # display the Articles Search tab
    # with article_search_tab:
    #    article_search.article_search()

    # display the PDF Search (My PDFs) tab
    # with pdf_tab:
    #    pdf_search.pdf_search()

    # display the Literature Review tab
    # with literature_review_tab:
    #    literature_review.literature_review()

    with st.container():
        updates.updates()