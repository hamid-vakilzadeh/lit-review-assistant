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

    # add a session state to keep track of tokens sent
    if 'tokens_sent' not in st.session_state:
        st.session_state.tokens_sent = 0

    # add a session state to keep track of tokens received
    if 'tokens_received' not in st.session_state:
        st.session_state.tokens_received = 0

    # add a session state to keep track of total tokens sent
    if 'total_tokens_sent' not in st.session_state:
        st.session_state.total_tokens_sent = 0

    # add a session state to keep track of total tokens received
    if 'total_tokens_received' not in st.session_state:
        st.session_state.total_tokens_received = 0

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

    # create a state to track the pdf summaries
    if 'pdf_summaries' not in st.session_state:
        st.session_state.pdf_summaries = {}