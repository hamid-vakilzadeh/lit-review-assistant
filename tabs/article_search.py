import re
import streamlit as st
from utils import documentSearch
from utils.ai import ai_completion
from utils.doi import get_apa_citation
from utils.funcs import pin_piece, unpin_piece
from pandas import read_csv
import json
import requests
import pandas as pd
from datetime import datetime
from utils.session_state_vars import bulk_search_column_order, bulk_search_column_config
from tabs.css import css_code


@st.cache_data
def get_journal_names():
    return read_csv('public/journal_names.csv').to_dict('records')


def prep_gpt_summary(
        document,
) -> list:
    messages = [
        {
            "role": "system",
            "content": "You are a research assistant and you should help the professor with their research. "
                       "You will be provided with an abstract. "
                       "Your task is to summarize the abstract. Use inline APA style to cite the paper once. "
                       "Provide a list of 3 to 5 very short bullet points to summarize the paper. "
                       "Keep your summary below 100 words."
        },
        {
            "role": "user",
            "content": (
                f"Summarize this is abstract in a few bullet points: <abstract>{document['text']}<abstract>\n"
                f"<citation>{document['citation'][0]}<citation>\n "
                f"Begin\n "
            )
        },
    ]

    return messages


def generate_completion(article):
    # first get citation for article by doi
    if article['id'] not in st.session_state.citations.keys():
        with st.session_state[f"{article['id']}_container"]:
            get_apa_citation(article)

    # add citation to article dict
    article['citation'] = [st.session_state.citations.get(article['id'])]

    # generate the prompt
    prompt = prep_gpt_summary(
        article,
    )

    try:
        response = ai_completion(
            messages=prompt,
            model=st.session_state.selected_model,
            temperature=0.3,
            # max_tokens=1500,
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
                    yield st.session_state.last_response

    except Exception as e:
        st.error(f"The AI is not responding. Please try again or choose another model.")
        st.stop()


def sort_results(sort_method):
    if st.session_state.article_search_results is not None:
        if sort_method == 'Relevance':
            return sorted(st.session_state.article_search_results,
                          key=lambda x: x['text'][1],
                          reverse=True)

        if sort_method == 'CrossRef Citations':
            return sorted(st.session_state.article_search_results,
                          key=lambda x: x['cite_counts'],
                          reverse=True)

        if sort_method == 'Year':
            return sorted(st.session_state.article_search_results,
                          key=lambda x: x['year'],
                          reverse=True)


# update the filter for the search
def update_filter():
    # create a dictionary of the selected years
    pass


@st.experimental_fragment
def article_search():
    css_code()
    st.subheader("Article Search")
    # user input for topic to search for
    # explain
    with st.expander(label="Search Box", expanded=True):
        st.markdown("Start with searching for articles that are relevant to your research topic: \n\n "
                    "- Search for a topic by entering a keyword or a phrase. \n "
                    "- Use quotation marks to search for an exact phrase (*e.g \"audit quality\"*). \n"
                    "- Use the logical operators *AND* and *OR* to narrow down your search. "
                    "(*e.g. \"audit quality\" AND \"earnings management\" will search for articles that contain both "
                    "audit quality and earnings management*). "
                    )
        with st.form(key="article_search_form"):

            st.session_state.number_of_articles = st.number_input(
                "**Number of articles**",
                min_value=1,
                max_value=100,
                value=4,
                step=1,
                key="num_articles"
            )

            # with sub_column2:
            # select data range as year
            st.slider(
                label="**Year**",
                min_value=1990,
                max_value=2024,
                value=[2000, 2024],
                step=1,
                key="year")

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

            # 3 columns for submit form button

            st.text_area(
                label="**DOI**",
                placeholder="Enter DOI(s) one per line",
                key="doi_search",
                label_visibility="collapsed",
            )

            st.markdown("OR")
            # a1.text_input(
            #    label="**author name**",
            #    placeholder=" author search (coming soon...)",
            #    key="author_search",
            #    label_visibility="collapsed",
            #    disabled=True
            # )

            # 3 columns for submit form button

            st.text_input(
                label="**Search a Topic**",
                placeholder="search for a topic, "
                            "e.g. "
                            "or 'audit quality and earnings management'",
                key="search",
                label_visibility="collapsed"
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

            article_search_button = st.form_submit_button(
                label="Search",
                type="primary",
                use_container_width=True,
            )

        if article_search_button:
            if st.session_state.search.strip() == "" and st.session_state.doi_search.strip() == "":
                st.toast(":red[Please Enter a Search Topic or a DOI.]", icon="⚠️")
                return
            else:
                msg = st.toast("Searching for articles...", icon="🔍")
                st.session_state.article_search_results = documentSearch.find_docs(
                    topic=st.session_state.search.strip(),
                    number_of_docs=st.session_state.number_of_articles,
                    year_range=[st.session_state.year[0], st.session_state.year[1]],
                    doi=st.session_state.doi_search.strip(),
                    journal=my_journals,
                    contains=exact_matched,
                    condition=logical_operator,
                    # author=st.session_state.author_search
                )
                msg.toast(f"Showing **{len(st.session_state.article_search_results)}** articles", icon="📚")
            if len(st.session_state.article_search_results) == 0:
                st.toast("No articles found. Please try again.", icon="❗")

        # display the articles
    with st.container(height=500):
        if not st.session_state.article_search_results:
            st.markdown("Search Results will be displayed here.")
        else:
            for article in st.session_state.article_search_results:
                # search the sql database for the article summary/bullet points
                st.markdown(f"**{article['title']}**, *{article['journal']} {article['year']}* {article['doi']}")

                st.markdown(f"*{article['authors']}*")

                # generate a state for the regenerate button
                if f"regenerate_{article['id']}" not in st.session_state:
                    st.session_state[f"regenerate_{article['id']}"] = False

                # write journal name
                st.markdown(
                    # f"**Relevance Score**: *{article['relevance']}%* | "
                    f"**CrossRef Citations**: *{article['cite_counts']}*"
                )

                # two columns for buttons
                left_column, right_column = st.columns(2)

                with left_column:
                    # if article is not added to notes show add notes
                    if article not in st.session_state.pinned_articles:
                        st.button(
                            label="📌 **pin**",
                            key=article['id'],
                            type='primary',
                            use_container_width=True,
                            on_click=pin_piece,
                            args=(article, st.session_state.pinned_articles,)
                        )

                    else:
                        # if already added to notes show remove notes
                        st.button(
                            label="↩️ **unpin**",
                            key=article['id'],
                            type='secondary',
                            use_container_width=True,
                            on_click=unpin_piece,
                            args=(article, st.session_state.pinned_articles,)

                        )

                with right_column:
                    # if article has a summary show regenerate summary
                    if article['id'] in st.session_state.summaries.keys():
                        st.button(
                            label="Regenerate Summary",
                            key=f"regenerate_{article['id']}",
                            type='secondary',
                            use_container_width=True
                        )

                # radio buttons for abstract or summary
                index = 0

                # set the default radio button to summary if the regenerate button is clicked
                if st.session_state[f"regenerate_{article['id']}"]:
                    index = 1

                st.radio(
                    label="Abstract or Summary",
                    options=['Abstract', 'Summary'],
                    key=f"radio_{article['id']}",
                    index=index,
                    horizontal=True,
                    label_visibility='collapsed'

                )
                # placeholder for summary and abstract
                st.session_state[f"{article['id']}_container"] = st.empty()

                # if radio button is abstract
                if st.session_state[f"radio_{article['id']}"] == 'Abstract':
                    st.session_state[f"{article['id']}_container"].markdown(
                        f'{article["text"]}'
                    )
                # if radio button is summary
                if st.session_state[f"radio_{article['id']}"] == 'Summary':
                    if st.session_state[f"regenerate_{article['id']}"]:
                        # stream the summary in the box
                        with st.session_state[f"{article['id']}_container"]:
                            for response_chunk in generate_completion(article=article):
                                st.session_state[f"{article['id']}_container"].markdown(f'{response_chunk}')

                        # save the summary in the session state
                        st.session_state.summaries[article['id']] = st.session_state.last_response

                        # delete the last response to avoid contamination
                        st.session_state.pop('last_response', None)

                    # if summary is already generated show it
                    elif article['id'] in st.session_state.summaries.keys():
                        st.session_state[f"{article['id']}_container"].markdown(
                            f'{st.session_state.summaries[article["id"]]}'
                        )

                    # if not generated show the button
                    elif article['id'] not in st.session_state.summaries.keys():
                        st.session_state[f"{article['id']}_container"].button(
                            label="Get AI Generated Summary",
                            key=f"summarize_{article['id']}",
                            type='secondary'
                        )

                        # if button is clicked generate the summary
                        if st.session_state[f"summarize_{article['id']}"]:

                            # stream the summary in the box
                            with st.session_state[f"{article['id']}_container"]:
                                for response_chunk in generate_completion(article=article):
                                    st.session_state[f"{article['id']}_container"].markdown(f'{response_chunk}')

                            # save the summary in the session state
                            st.session_state.summaries[article['id']] = st.session_state.last_response

                            # delete the last response to avoid contamination
                            st.session_state.pop('last_response', None)

                            # update the session state
                            st.rerun()

                st.markdown('---')

                # st.write(st.session_state)


def semantic_bulk_search(
        search_term: str = "",
        year_start: datetime = "",
        year_end: datetime = "",
        at_least_citations: int = 0,
        venues: list = None,
        token: str = None,
        sort_by: str = 'citationCount:desc',
):
    venues_list = None
    if venues:
        venues_list = ','.join(venues)
    if year_end == datetime.now():
        year_end = ''

    parameters = {'query': search_term,
                  'publicationDateOrYear': f"{year_start}:{year_end}",
                  'minCitationCount': at_least_citations,
                  'venue': venues_list,
                  'fieldsOfStudy': 'Business',
                  'fields': 'title,authors,venue,year,citationCount,s2FieldsOfStudy,abstract,externalIds',
                  'sort': sort_by,
                  }
    if token:
        parameters['token'] = token
    response = requests.get(
        url=f"https://api.semanticscholar.org/graph/v1/paper/search/bulk",
        headers={'x-api-key': st.secrets['semantic_scholar']},
        params=parameters
    )
    if response.status_code != 200:
        return None
    return response.json()


def get_external_url(x):
    if "DOI" in x:
        return f"https://doi.org/{x['DOI']}"
    elif "ArXiv" in x:
        return f"https://arxiv.org/abs/{x['ArXiv']}"
    elif "PMID" in x:
        return f"https://pubmed.ncbi.nlm.nih.gov/{x['PMID']}"
    elif "MAG" in x:
        return f"https://academic.microsoft.com/paper/{x['MAG']}"
    elif "DBLP" in x:
        return f"https://dblp.org/rec/{x['DBLP']}"
    elif "CorpusId" in x:
        return f"https://www.semanticscholar.org/paper/{x['CorpusId']}"
    else:
        return None


def bulk_search():
    with st.form(key="advanced_search"):
        st.subheader("Advanced Search")
        search_term = st.text_input(
            label="**Search**",
            placeholder="search for a topic",
            key="semantic_bulk_search",
            label_visibility="collapsed",
        )
        sort_col, journal_col = st.columns(2)
        sort_options = {
            "Publication Date (Newest to Oldest)": "publicationDate:desc",
            "Publication Date (Oldest to Newest)": "publicationDate:asc",
            "Citation Count (Highest to Lowest)": "citationCount:desc",
            "Citation Count (Lowest to Highest)": "citationCount:asc",
        }
        sort_by = sort_col.selectbox(
            label="Sort By",
            options=sort_options.keys(),
            key="sort_by",
        )

        journals = journal_col.multiselect(
            label="Journals",
            options=st.session_state.venues,
            key='journals',
            disabled=False
        )
        col1, col2, col3 = st.columns(3)
        date_start = col1.date_input(
            label="Date Start",
            min_value=datetime(1950, 1, 1),
            max_value=datetime.now(),
            value=datetime(2000, 1, 1),
            key="date_start"
        )

        date_end = col2.date_input(
            label="Date End",
            min_value=date_start,
            max_value=datetime.now(),
            value=datetime.now(),
            key="date_end"
        )

        at_least_citations = col3.number_input(
            label="Cited at least",
            min_value=0,
            value=0,
            step=1,
            key="at_least_citations"
        )

        search_button = st.form_submit_button(
            label="Search",
            type="primary",
            use_container_width=False,
            on_click=lambda: st.session_state.pop('bulk_search_response', None)
        )

    if search_button and search_term.strip() != "":
        st.session_state.bulk_search_response = semantic_bulk_search(
            search_term=search_term,
            sort_by=sort_options[sort_by],
            year_start=date_start,
            year_end=date_end,
            at_least_citations=at_least_citations,
            venues=journals
        )
    elif search_button and search_term.strip() == "":
        st.session_state.total_results = 0
        st.warning("Please enter a search term.")

    if 'bulk_search_response' in st.session_state:
        st.session_state.total_results = st.session_state.bulk_search_response['total']
        st.session_state.bulk_search_token = st.session_state.bulk_search_response['token']
        data_to_show = pd.DataFrame(st.session_state.bulk_search_response.copy()['data'])
        if len(data_to_show) == 0:
            st.warning("No results found.")
        else:
            data_to_show['s2FieldsOfStudyUnique'] = data_to_show.s2FieldsOfStudy.apply(
                lambda x: list({d['category'] for d in x} if x else []))
            data_to_show['authorNames'] = data_to_show['authors'].apply(
                lambda x: [d['name'] for d in x])
            data_to_show = data_to_show.drop(columns=['s2FieldsOfStudy', 'authors'])
            data_to_show.set_index('paperId', inplace=True)
            data_to_show['source'] = data_to_show['externalIds'].apply(get_external_url)
            # rename columns
            data_to_show.rename(
                columns={
                    'authorNames': 'authors',
                    'venue': 'journal',
                    'citationCount': 'citations',
                    's2FieldsOfStudyUnique': 'topics',
                },
                inplace=True
            )
            st.session_state.data_to_show = data_to_show.copy()
            st.session_state.pop('bulk_search_response', None)

    if 'data_to_show' in st.session_state:
        return_col, next_col = st.columns(2, gap='large')
        if len(st.session_state.data_to_show) == 1000:
            st.success("More than a 1000 results found. Try to narrow down your search.")
        else:
            st.success(f"{len(st.session_state.data_to_show)} results found.")
        st.write('Select up to 20 papers to add to your chat.')
        results = st.dataframe(
            hide_index=True,
            data=st.session_state.data_to_show,

            column_order=bulk_search_column_order(),
            column_config=bulk_search_column_config(),
            selection_mode="multi-row",
            on_select='rerun',
            use_container_width=True,

        )

        papers = results.selection.rows
        disabled = False
        if len(papers) > 20:
            disabled = True
            st.error("You can only select up to 20 papers at a time.")

        return_col.button(
            label='Finish and Return to Chat',
            type='primary',
            key='close_advanced_search',
            use_container_width=True,
            disabled=disabled
        )

        selected_papers = st.session_state.data_to_show.iloc[papers]

        if st.session_state.close_advanced_search:
            st.session_state.pinned_articles_ss = \
                pd.concat([st.session_state.pinned_articles_ss, selected_papers])
            st.session_state.pinned_articles_ss.reset_index(inplace=True)
            st.session_state.pinned_articles_ss.drop_duplicates(
                subset=['paperId'],
                inplace=True)
            st.session_state.pinned_articles_ss.set_index('paperId', inplace=True)

            # add_pd_to_lit_review(st.session_state.pinned_articles_ss)
            st.rerun()


def advanced_search():
    css_code()
    bulk_search_tab, author_search_tab, paper_search_tab = st.tabs(
        ["Topic Search", "Author Search", "Paper information"]
    )
    with bulk_search_tab:
        bulk_search()
    # st.write(st.session_state)
