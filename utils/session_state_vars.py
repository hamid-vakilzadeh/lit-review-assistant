import streamlit as st


def ensure_session_state_vars():
    # add a session state to store the article search results
    if 'article_search_results' not in st.session_state:
        st.session_state.article_search_results = []

    # add a session state to keep track of the added articles
    if 'pinned_articles' not in st.session_state:
        st.session_state.pinned_articles = []

    # create a state to track the pdf summaries selected for review
    if 'pinned_pdfs' not in st.session_state:
        st.session_state.pinned_pdfs = []

    # create a state to track the pdf summaries selected for review
    if 'pinned_reviews' not in st.session_state:
        st.session_state.pinned_reviews = []

    # add a session state to store the pieces for the review
    if 'review_pieces' not in st.session_state:
        st.session_state.review_pieces = []

    # add a session state to keep track of previous reviews
    if 'previous_reviews' not in st.session_state:
        st.session_state.previous_reviews = []

    # add a session state to keep track of summaries generated
    if 'summaries' not in st.session_state:
        st.session_state.summaries = {}

    # add a session state to keep track of citations
    if 'citations' not in st.session_state:
        st.session_state.citations = {}

    # create a state to track the pdf summaries generated
    if 'pdf_history' not in st.session_state:
        st.session_state.pdf_history = []

    if 'included_articles' not in st.session_state:
        st.session_state.included_articles = {}

    # session state for last PDF Q&A question
    if 'last_pdf_qa_response' not in st.session_state:
        st.session_state.last_pdf_qa_response = ''

    # session state for last PDF summary
    if 'last_pdf_summary_response' not in st.session_state:
        st.session_state.last_pdf_summary_response = ''

    if "messages_to_api" not in st.session_state:
        st.session_state.messages_to_api = [
            {"role": "system", "content": 'You are a research assistant and you should help '
                                          'the professor with his research.'
                                          'You are a research assistant and you should help '
                                          'the professor with his research. '
                                          'Your job is to identify themes and write a coherent literature review. '
                                          'You are encouraged to identify points of tension.\n'
             }
        ]

