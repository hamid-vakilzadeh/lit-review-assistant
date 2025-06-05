import pandas as pd
import streamlit as st
import json
from utils.local_storage import initialize_local_storage
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
            journals = df[df['type'] == 'journal']['name'].tolist()
            journals.sort()
            return journals


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

    # Initialize local storage for chat management
    initialize_local_storage()

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
    
    # Set default model if not already set
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = 'openai/gpt-4o'
    
    # RAG-related session state
    if 'rag_documents' not in st.session_state:
        st.session_state.rag_documents = []
    
    if 'rag_abstracts' not in st.session_state:
        st.session_state.rag_abstracts = []
    
    if 'rag_query_results' not in st.session_state:
        st.session_state.rag_query_results = []


def bulk_search_column_order():
    return [
        'source',
        'title',
        'authors',
        'journal',
        'year',
        'citations',
        'topics',
        'abstract',
    ]


def bulk_search_column_config():
    return {
                'source': st.column_config.LinkColumn(
                    label="Source",
                    display_text="open",
                ),
                'title': st.column_config.TextColumn(
                    label="Title",
                    disabled=True,
                ),
                'authors': st.column_config.ListColumn(
                    label="Authors",
                ),
                'journal': st.column_config.TextColumn(
                    label="Journal",
                    disabled=True,
                ),
                'year': st.column_config.TextColumn(
                    label="Year",
                    disabled=True,
                ),
                'citations': st.column_config.TextColumn(
                    label="Citations",
                    disabled=True,
                ),
                'topics': st.column_config.ListColumn(
                    label="Topics",
                ),
                'abstract': st.column_config.TextColumn(
                    label="Abstract",
                    disabled=True,
                ),

            }
