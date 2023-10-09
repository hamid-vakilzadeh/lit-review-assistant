import streamlit as st
from tabs import sidebar, article_search, pdf_search, literature_review
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

    # sidebar.show_sidebar()

    # display the header and general settings
    with st.container():
        # The header
        st.header("AAIRA: Accounting AI Research Assistant")

        # The description
        st.markdown(
            """
            This app is designed to assist accounting researchers in finding and organizing accounting literature.
            """
        )
