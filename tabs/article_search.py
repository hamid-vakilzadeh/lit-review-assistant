import re
import streamlit as st
from tools import documentSearch
from .openai_api import chat_completion, update_cost, num_tokens_from_messages
# from tools.createTables import get_journal_names
from tools.doi import get_citation
from pandas import read_csv
from typing import Optional


@st.cache_data
def get_journal_names():
    return read_csv('public/journal_names.csv').to_dict('records')


def prep_gpt_summary(
        document,
        bullet_point: bool,
        number_of_words: Optional[int] = None
) -> list:

    if bullet_point:
        summary_style = 'provide a list of 3 to 5 very very short ' \
                        'bullet points of the major points of the study and its findings. ' \
                        'always use bullet points, unless it absolutely makes no sense.\n'
    else:
        summary_style = 'provide a very short summary of the research article and  its findings. Do not ramble!\n'

    if number_of_words:
        summary_style += f'Keep your summary below {number_of_words} words long.\n'

    messages = [
        {"role": "system", "content": "You are a research assistant and you should help "
                                      "the professor with his research."},
        {"role": "user", "content": (f"{summary_style}"
                                     "always use APA style and always mention the citation.\n"
                                     "e.g. ... et al. (2022) find that ... or similar.\n"
                                     f"This is the abstract: {document['doc'][0].page_content}\n"
                                     f"and this is the reference: {document['doc'][0].metadata['citation']}\n "
                                     f"Begin\n "
                                     )
         },
    ]

    return messages


def sort_results(sort_method):
    if st.session_state.relevant_articles is not None:
        if sort_method == 'Relevance':
            return sorted(st.session_state.relevant_articles,
                          key=lambda x: x['doc'][1],
                          reverse=True)

        if sort_method == 'CrossRef Citations':
            return sorted(st.session_state.relevant_articles,
                          key=lambda x: x['cite_counts'],
                          reverse=True)

        if sort_method == 'Year':
            return sorted(st.session_state.relevant_articles,
                          key=lambda x: x['year'],
                          reverse=True)


# add to notes
def add_to_notes(paper):
    st.session_state.notes.append(paper)
    st.session_state.added_articles.append(paper['doc'][0].metadata['doi'])


# remove from notes
def remove_from_notes(paper):
    st.session_state.notes.remove(paper)
    st.session_state.added_articles.remove(
        paper['doc'][0].metadata['doi']
    )


# update the filter for the search
def update_filter():
    # create a dictionary of the selected years
    pass


def article_search():
    st.subheader("Article Search")
    # user input for topic to search for
    user_input = st.text_input(
        label="**Search a Topic**",
        placeholder="search for a topic, "
                    "e.g. "
                    "or 'audit quality and earnings management'",
        key="search",
    )

    left_column, right_column = st.columns(2)

    with left_column:
        sub_column1, sub_column2 = st.columns([2, 3])
        with sub_column1:
            st.session_state.number_of_articles = st.number_input(
                "**Number of articles**",
                min_value=1,
                max_value=100,
                value=4,
                step=1,
                key="num_articles"
            )

        with sub_column2:
            # select data range as year
            st.slider(
                label="**Year**",
                min_value=1990,
                max_value=2023,
                value=[2000, 2023],
                step=1,
                key="year")

            st.session_state.include_only = {
                'year': {'$in': list(range(st.session_state.year[0], st.session_state.year[1]))}}

    with right_column:
        st.multiselect(
            label="**Select Journals** (leave empty for all journals)",
            options=get_journal_names(),
            format_func=lambda x: f"{x['journal']} ({x['number_of_articles']} articles)",
            key='selected_journal',
            disabled=False
        )

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

    if st.button(
            label="Search",
            type="primary"
    ):
        if st.session_state.search == "":
            st.error("Please enter a search topic")
        else:
            st.session_state.relevant_articles = documentSearch.find_docs(
                topic=user_input,
                number_of_docs=st.session_state.number_of_articles,
                # include_only={"where": {"$or": [{"year": "2021"}, {"year": "2000"}]}}
                # include_only={'$or': [{'year': '2021'}, {'year': '2020'}], 'journal': 'The Accounting Review'}
            )

        # get summary from session state if it exists
        for article in st.session_state.relevant_articles:
            if article['doc'][0].metadata['doi'] in st.session_state.added_articles:
                article['summary'] = st.session_state.notes[
                    st.session_state.added_articles.index(article['doc'][0].metadata['doi'])]['summary']

    # display the articles
    for article in st.session_state.relevant_articles:
        col1, col2 = st.columns([5, 1])
        with col1:
            # search the sql database for the article summary/bullet points
            st.markdown(f"**{article['doc'][0].metadata['title']}**")
            st.markdown(
                f"*{article['doc'][0].metadata['journal']}*, "
                f" **{article['doc'][0].metadata['year']}**")
            st.markdown('**Summary**')
            ai_response = st.empty()

            # get citation from article by doi
            article['doc'][0].metadata['citation'] = get_citation(
                article['doc'][0].metadata['doi'])

        with col2:
            # write journal name
            st.metric(
                label='Relevance Score',
                value=f"{(round(1 - article['doc'][1], 3) * 100)}%"
            )

            # number of citations
            st.metric(
                label='CrossRef Citations',
                value=f"{article['cite_counts']}"
            )

        with col1:
            prompt = prep_gpt_summary(
                article,
                bullet_point=True,
                number_of_words=st.session_state.max_words
            )

            # get summary of the abstract
            if 'summary' not in article:
                # count the number of tokens in the prompt
                st.session_state.tokens_sent += num_tokens_from_messages(prompt)

                response = chat_completion(
                    messages=prompt,
                    model=st.session_state.selected_model,
                    temperature=st.session_state.temperature,
                    max_tokens=int(st.session_state.max_words*4/3),
                    stream=True
                )

                # stream the response
                collected_chunks = []
                report = []
                for chunk in response:
                    collected_chunks.append(chunk)  # save the event response
                    if 'content' in chunk['choices'][0]['delta']:
                        report.append(chunk.choices[0]['delta']['content'])
                        st.session_state.last_response = "".join(report).strip()
                        ai_response.markdown(f'{st.session_state.last_response}')
                article['summary'] = st.session_state.last_response

                # count the number of tokens in the response
                st.session_state.tokens_received += len(collected_chunks)
                update_cost()

            else:
                ai_response.markdown(f'{article["summary"]}')

            # Show citation
            st.markdown(f"**{re.sub(r'https.*', '', article['doc'][0].metadata['citation']).strip()}**")
            st.markdown(f"**DOI**: {article['doc'][0].metadata['doi']}")

        with col2:
            # add to notes
            if len(st.session_state.relevant_articles) > 0:
                if article['doc'][0].metadata['doi'] not in st.session_state.added_articles:
                    st.button(
                        label="Add to Notes",
                        key=article['doc'][0].metadata['doi'],
                        help="Add this article to your notes for literature review",
                        type='primary',
                        on_click=add_to_notes,
                        args=(article,)
                    )

                else:  # if already added to notes
                    st.button(
                        label="Remove",
                        key=article['doc'][0].metadata['doi'],
                        help="Remove this article from your notes for literature review",
                        type='secondary',
                        on_click=remove_from_notes,
                        args=(article,)
                    )

        st.markdown("----")
