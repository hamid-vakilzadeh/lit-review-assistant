import re
import streamlit as st
from utils import documentSearch
from utils.ai import ai_completion
from utils.doi import get_apa_citation
from utils.funcs import pin_piece, unpin_piece, add_to_context, set_command_none
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
                                     f"This is the abstract: {document['text']}\n"
                                     f"and this is the reference: {document['citation'][0]}\n "
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
        bullet_point=True,
        number_of_words=st.session_state.max_words
    )

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
                yield st.session_state.last_response


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


def article_search(show_context: bool = False):
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

            # 3 columns for submit form button
            a1, a2 = st.columns([5, 1])

            a1.text_input(
                label="**DOI**",
                placeholder="Enter a DOI",
                key="doi_search",
                label_visibility="collapsed",
            )


            a1.text_input(
                label="**author name**",
                placeholder=" author search (coming soon...)",
                key="author_search",
                label_visibility="collapsed",
                disabled=True
            )

            # 3 colmns for submit form button
            s1, s2 = st.columns([5, 1])

            s1.text_input(
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

            with s2:
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

        if show_context:
            st.markdown('You can renew your search and the pinned items will be saved. '
                        'When you are finished, click on the button below to add the articles to your chat.'
                        )
            # two columns for buttons
            left_column, right_column = st.columns(2)

            # show add to context button
            add_to_context_button_status = True
            if len(st.session_state.pinned_articles) > 0:
                add_to_context_button_status = False

            with left_column:
                st.button(
                    label="✅ Add and Go to Chat",
                    key="add_to_context",
                    type='secondary',
                    disabled=add_to_context_button_status,
                    use_container_width=True,
                    on_click=add_to_context,
                    args=(st.session_state.pinned_articles,),
                )

            with right_column:
                st.button(
                    label="❌ Close and Clear",
                    key="close_search",
                    type='primary',
                    use_container_width=True,
                    on_click=lambda: set_command_none(),
                )
            # st.write(st.session_state)
