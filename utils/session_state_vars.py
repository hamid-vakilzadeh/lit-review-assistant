import streamlit as st
import json
import pyrebase
from google.oauth2 import service_account
from utils.firestore_db import firestore, create_new_profile, add_user_to_db
from time import time


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

    if "db" not in st.session_state:
        key_dict = json.loads(st.secrets["textkey"])
        creds = service_account.Credentials.from_service_account_info(key_dict)
        st.session_state.db = firestore.Client(credentials=creds, project="lit-review-d9a4b")

    if 'firebase' not in st.session_state:
        pyrebaseConfig = json.loads(st.secrets["pyrebaseConfig"])
        st.session_state.firebase = pyrebase.initialize_app(pyrebaseConfig)

    if 'auth' not in st.session_state:
        st.session_state.auth = st.session_state.firebase.auth()

    if 'user' in st.session_state and 'profile_details' not in st.session_state:
        create_new_profile(st.session_state.db, st.session_state.user['localId'])

    if 'session_start_time' in st.session_state:
        if time() - st.session_state.session_start_time > 3000:
            st.session_state.user = st.session_state.auth.refresh(st.session_state.user['refreshToken'])

        elif time() - st.session_state.session_start_time > 3600:
            st.session_state.clear()
            st.rerun()
