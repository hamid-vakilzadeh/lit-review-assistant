import pandas as pd
import streamlit as st
import json
import pyrebase
from google.oauth2 import service_account
from google.cloud import firestore
from utils.firestore_db import create_new_profile, add_user_to_db
from time import time
import zipfile
import json


@st.cache_data(show_spinner=False)
def get_venues():
    zip_file_path = 'public/venues.json.zip'
    # Open the ZIP file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        # Get the name of the only file in the ZIP archive
        file_name = zip_ref.namelist()[0]

        # Read the JSON file into a DataFrame
        with zip_ref.open(file_name) as json_file:
            df = pd.read_json(json_file, lines=True)
            return df[df['type'] == 'journal']['name'].tolist()


@st.cache_data(show_spinner=False)
def get_venues():
    data = pd.read_json('public/venues.json', lines=True)
    return data[data['type'] == 'journal']['name'].tolist()


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
            {
                "role": "system",
                "content": "You are a research assistant and you should help the professor with their research. "
                           "You will be provided with documents in the chat and some requests. Always refer to the context of the chat "
                           "for papers. Focus on the papers that the user provides as they change. Apologies are not necessary. "
                           "NEVER EVER use solely your own knowledge to answer questions. "
                           "Your task is to answer the question using only the provided research articles and to cite the passage(s) "
                           "of the document used to answer the question in inline APA style. If the document does not contain the "
                           "information needed to answer this question then simply write: cannot answer because the context "
                           "does not contain the information. "
                           "If an answer to the question is provided, it must be annotated with a citation. "
            }
        ]

    if "messages_to_api_context" not in st.session_state:
        st.session_state.messages_to_api_context = []

    if "messages_to_interface_context" not in st.session_state:
        st.session_state.messages_to_interface_context = []

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

    if 'change_name' not in st.session_state:
        st.session_state.change_name = False

    if 'show_search_dialog' not in st.session_state:
        st.session_state.show_search_dialog = False

    if 'pinned_articles_ss' not in st.session_state:
        st.session_state.pinned_articles_ss = pd.DataFrame()

    if 'lit_review_pd' not in st.session_state:
        st.session_state.lit_review_pd = pd.DataFrame()
    if 'venues' not in st.session_state:
        st.session_state.venues = get_venues()


def column_order():
    return [
        'Source',
        'title',
        'authorNames',
        'venue',
        'year',
        'citationCount',
        's2FieldsOfStudyUnique',
        'abstract',
    ]


def column_config():
    return {
                'Source': st.column_config.LinkColumn(
                    label="Source",
                    display_text="open",
                ),
                'title': st.column_config.TextColumn(
                    label="Title",
                    disabled=True,
                ),
                'authorNames': st.column_config.ListColumn(
                    label="Authors",
                ),
                'venue': st.column_config.TextColumn(
                    label="Journal",
                    disabled=True,
                ),
                'year': st.column_config.TextColumn(
                    label="Year",
                    disabled=True,
                ),
                'citationCount': st.column_config.TextColumn(
                    label="Citation Count",
                    disabled=True,
                ),
                's2FieldsOfStudyUnique': st.column_config.ListColumn(
                    label="Fields of Study",
                ),
                'abstract': st.column_config.TextColumn(
                    label="Abstract",
                    disabled=True,
                ),

            }
