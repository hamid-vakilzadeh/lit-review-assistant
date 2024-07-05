import re
import streamlit as st
from utils import documentSearch
from utils.ai import ai_completion
from utils.doi import get_apa_citation
from utils.funcs import pin_piece, unpin_piece
from pandas import read_csv
import json


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


def article_search():
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
