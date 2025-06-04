import pandas as pd
import streamlit as st
from utils.funcs import review_action_buttons, add_to_lit_review
from utils.session_state_vars import bulk_search_column_config, bulk_search_column_order
from utils.session_state_vars import ensure_session_state_vars

ensure_session_state_vars()


def choose_model():
    # Choose the model to use for generating the response
    chosen_model = st.selectbox(
        label='Model Name',
        options=[
            'OpenAI: GPT-4o',
            'Anthropic: Claude 3.5 Sonnet',
            'Google: Gemini Flash 1.5',
        ],
    )

    if chosen_model == 'OpenAI: GPT-4o':
        st.session_state.selected_model = 'openai/gpt-4o'
    if chosen_model == 'Anthropic: Claude 3.5 Sonnet':
        st.session_state.selected_model = 'anthropic/claude-3.5-sonnet'
    if chosen_model == 'Google: Gemini Flash 1.5':
        st.session_state.selected_model = 'google/gemini-flash-1.5'


def delete_pinned_articles_ss():
    st.session_state.pinned_articles_ss = pd.DataFrame()
    st.session_state.review_pieces = []
    st.session_state.messages_to_interface_context = []
    st.session_state.messages_to_api_context = []


def show_sidebar():
    with st.expander("📌 Pinboard", expanded=True):
        with st.container(border=False):
            # add delete button to clean pinned articles
            st.markdown("Keep track of the research papers you have found in search.")

            if len(st.session_state.pinned_articles_ss) == 0:
                st.error("Context is empty. "
                         "Go to  **Research Tools > Advanced Search** to search.")

            if len(st.session_state.pinned_articles_ss) > 0:
                st.markdown("You can only select up to 20 articles for review but you can keep all your search results here. "
                            "You can also download the pinned articles as a CSV file.")
                st.button(
                    label="🗑️ **Remove all papers**",
                    key="clear_pinned_articles",
                    type='secondary',
                    on_click=lambda: delete_pinned_articles_ss(),
                )
                selected_for_review = st.dataframe(
                    st.session_state.pinned_articles_ss,
                    column_config=bulk_search_column_config(),
                    column_order=bulk_search_column_order(),
                    hide_index=True,
                    on_select='rerun',
                    selection_mode='multi-row'
                )

                st.session_state.selected_for_review = selected_for_review.selection.rows
                st.session_state.review_pieces = []
                st.session_state.messages_to_interface_context = []
                st.session_state.messages_to_api_context = []

                # stop if len of selected_for_review is more than 20
                if len(st.session_state.selected_for_review) > 20:
                    st.error("You can only select up to 20 articles for review.")
                    st.stop()

                dataframe = st.session_state.pinned_articles_ss.copy()
                dataframe.rename(columns={
                    'abstract': 'text',
                    'citations': 'cite_counts',
                    'authors': 'authors',
                    "source": "doi",

                }, inplace=True)

                papers_included = dataframe.iloc[st.session_state.selected_for_review]

                included_pd_to_dict = papers_included.to_dict(orient='records')
                for article in included_pd_to_dict:
                    if article not in st.session_state.review_pieces:
                        add_to_lit_review(article)

            for article in st.session_state.pinned_articles:
                st.markdown(f"**{article['title']}**")
                review_action_buttons(article, st.session_state.pinned_articles)
                st.markdown(f"{article['doi'].strip()}", )
                st.markdown(f"{article['text']}")
                st.markdown("---")
