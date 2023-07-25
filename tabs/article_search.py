import re
import streamlit as st
from tools import documentSearch
from tools.ai import ai_completion
# from tools.createTables import get_journal_names
from tools.doi import get_citation
from pandas import read_csv
from typing import Optional
import json


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
                                     f"This is the abstract: {document['doc']}\n"
                                     f"and this is the reference: {document['citation']}\n "
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
    st.session_state.added_articles.append(paper['id'])


# remove from notes
def remove_from_notes(paper):
    st.session_state.notes.remove(paper)
    st.session_state.added_articles.remove(
        paper['id']
    )


# update the filter for the search
def update_filter():
    # create a dictionary of the selected years
    pass


def article_search():
    st.subheader("Article Search")
    # user input for topic to search for
    # explain
    st.markdown("Start with searching for articles that are relevant to your research topic: \n\n "
                "- Search for a topic by entering a keyword or a phrase. \n "
                "- Use quotation marks to search for an exact phrase (*e.g \"audit quality\"*). \n"
                "- Use the logical operators *AND* and *OR* to narrow down your search. "
                "(*e.g. \"audit quality\" AND \"earnings management\" will search for articles that contain both "
                "audit quality and earnings management*). "
                )

    user_input = st.text_input(
        label="**Search a Topic**",
        placeholder="search for a topic, "
                    "e.g. "
                    "or 'audit quality and earnings management'",
        key="search",
    )

    # find all exact phrase requested
    logical_operator = None
    exact_matched = []

    if st.session_state.search.strip() != "":
        # find exact search matches:
        pattern = r'"([^"]+)"'

        exact_matched = re.findall(pattern, st.session_state.search)

        # find the condition specified
        pattern = r'\b(AND|OR)\b'

        # condition specified
        cond = re.search(pattern, st.session_state.search)

        if cond:
            logical_operator = cond.group(1)
        else:
            logical_operator = None


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

    with right_column:
        st.multiselect(
            label="**Select Journals** (leave empty for all journals)",
            options=get_journal_names(),
            format_func=lambda x: f"{x['journal']} ({x['number_of_articles']} articles)",
            key='selected_journal',
            disabled=False
        )
        if len(st.session_state.selected_journal) > 0:
            my_journals = [{k: v for k, v in d.items() if k != 'number_of_articles'} for d in st.session_state.selected_journal]
        else:
            my_journals = None


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

    if st.button(
            label="Search",
            type="primary"
    ):
        if st.session_state.search.strip() == "":
            st.error("Please enter a search topic")
        else:
            st.session_state.relevant_articles = documentSearch.find_docs(
                topic=user_input,
                number_of_docs=st.session_state.number_of_articles,
                year_range=[st.session_state.year[0], st.session_state.year[1]],
                journal=my_journals,
                contains=exact_matched,
                condition=logical_operator
            )

    if len(st.session_state.relevant_articles) == 0:
        st.info("No articles found. Please try again.")

    # display the articles
    for article in st.session_state.relevant_articles:
        col1, col2 = st.columns([5, 1])
        with col1:
            # search the sql database for the article summary/bullet points
            st.markdown(f"**{article['title']}**, *{article['journal']} {article['year']}* {article['doi']}")

            st.session_state[f"{article['id']}_container"] = st.empty()
            if article['id'] in st.session_state.summaries.keys():
                st.session_state[f"{article['id']}_container"].markdown(f'{st.session_state.summaries[article["id"]]}')

        with col2:
            # write journal name
            st.metric(
                label='Relevance Score',
                value=f"{round((1 - round(article['distance'], 2)) * 100)}%"
            )

            # number of citations
            st.metric(
                label='CrossRef Citations',
                value=f"{article['cite_counts']}"
            )

            if len(st.session_state.relevant_articles) > 0:
                if article['id'] not in st.session_state.added_articles:
                    st.button(
                        label="Add to Notes",
                        key=article['id'],
                        help="Add this article to your notes for literature review",
                        type='primary',
                        on_click=add_to_notes,
                        args=(article,)
                    )

                else:  # if already added to notes
                    st.button(
                        label="Remove",
                        key=article['id'],
                        help="Remove this article from your notes for literature review",
                        type='secondary',
                        on_click=remove_from_notes,
                        args=(article,)
                    )
        st.markdown('---')

    for article in st.session_state.relevant_articles:

        # get summary of the abstract
        if article['id'] not in st.session_state.summaries.keys():
            st.session_state[f"{article['id']}_container"].button(
                label="Get AI Generated Summary",
                key=f"summarize_{article['id']}",
                type='secondary'
            )

            if st.session_state[f"summarize_{article['id']}"]:
                # get citation from article by doi
                if article['id'] not in st.session_state.citations.keys():
                    with st.session_state[f"{article['id']}_container"]:
                        st.session_state.citations[article['id']] = get_citation(article['doi'])

                article['citation'] = st.session_state.citations.get(article['id'])

                prompt = prep_gpt_summary(
                    article,
                    bullet_point=True,
                    number_of_words=st.session_state.max_words
                )

                # count the number of tokens in the prompt

                with st.session_state[f"{article['id']}_container"]:
                    response = ai_completion(
                        messages=prompt,
                        model=st.session_state.selected_model,
                        temperature=st.session_state.temperature,
                        max_tokens=1500,
                        stream=True,
                    )
                    collected_chunks = []
                    report = []
                    for line in response.iter_lines():
                        if line and 'data' in line.decode('utf-8'):
                            content = line.decode('utf-8').replace('data: ', '')
                            if 'content' in content:
                                message = json.loads(content, strict=False)
                                collected_chunks.append(message)  # save the event response
                                report.append(message['choices'][0]['delta']['content'])
                                st.session_state.last_response = "".join(report).strip()
                                st.session_state[f"{article['id']}_container"].markdown(f'{st.session_state.last_response}')

                st.session_state.summaries[article['id']] = st.session_state.last_response

                # delete the last response
                st.session_state.pop('last_response', None)

                if st.session_state.selected_model == 'google/palm-2-chat-bison':
                    st.experimental_rerun()

        else:
            with st.session_state[f"{article['id']}_container"]:
                st.markdown('**Summary**')
                st.markdown(
                    f'{st.session_state.summaries[article["id"]]}')

        # Show citation
        # st.markdown(f"{re.sub(r'https.*', '', article['citation']).strip()}")



    #st.write(st.session_state)