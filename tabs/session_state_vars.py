import streamlit as st


def ensure_session_state_vars():
    # add a session state to store the relevant articles
    if 'relevant_articles' not in st.session_state:
        st.session_state.relevant_articles = []

    # add a session state to store the notes
    if 'notes' not in st.session_state:
        st.session_state.notes = []

    # add a session state to keep track of the added articles
    if 'added_articles' not in st.session_state:
        st.session_state.added_articles = []

    # add a session state to keep track of previous reviews
    if 'previous_reviews' not in st.session_state:
        st.session_state.previous_reviews = []

    # add a session state to keep track of final pieces
    if 'final_pieces' not in st.session_state:
        st.session_state.final_pieces = []

    # add a session state to keep track of keep review button label
    if 'keep_review_label' not in st.session_state:
        st.session_state.keep_review_label = "Keep"

    # add a session state to keep track of summaries generated
    if 'summaries' not in st.session_state:
        st.session_state.summaries = {}

    # add a session state to keep track of citations
    if 'citations' not in st.session_state:
        st.session_state.citations = {}

    # create a state to track the pdf summaries generated
    if 'pdf_summaries' not in st.session_state:
        st.session_state.pdf_summaries = {}

    # create a state to track the pdf summaries selected for review
    if 'pdf_summaries_selected' not in st.session_state:
        st.session_state.pdf_summaries_selected = {}

    if 'included_articles' not in st.session_state:
        st.session_state.included_articles = {}
