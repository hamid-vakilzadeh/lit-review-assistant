import re
import datetime
import streamlit as st
from utils.ai import ai_completion
from utils.doi import get_apa_citation
from typing import Optional
import json
from utils.funcs import show_pin_buttons


def lit_review_message(
        articles: dict,
        additional_instructions: str,
        number_of_words: Optional[int] = None
) -> list:
    """
    Create a list of messages to send to the OpenAI API
    :param articles: list of articles to send to the OpenAI API
    :param additional_instructions: additional instructions to send to the OpenAI API
    :type additional_instructions: str
    :param number_of_words: response cutoff as the number of words to OpenAI API
    :type number_of_words: int
    :return: list of messages to send to the OpenAI API
    :rtype: list
    """
    all_articles = []
    for article in articles:
        # if citation is not already in the session state, get it
        article_citation = article.get('citation', st.session_state.citations.get(article['id'], None))
        if not article_citation:
            get_apa_citation(article)
            article_citation = st.session_state.citations.get(article['id'], None)
            article['citation'] = [article_citation]

        if isinstance(article_citation, list):
            article_citation = "\n".join(article_citation)

        article_text = article.get('summary', article.get('text', ''))

        all_articles.append(
            f"Piece {articles.index(article)+1} texts: {article_text}\n"
            f"Piece {articles.index(article)+1} citation(s): {re.sub(r'https.*', '', article_citation).strip()}:\n "
        )

    all_articles = "\n".join(all_articles)

    job_request = 'You are provided summaries of several research articles. ' \
                  'Your job is to identify themes and write a coherent literature review. ' \
                  'You are encouraged to identify points of tension.\n'

    if number_of_words:
        job_request += f'Keep your literature review below {number_of_words} words long.\n'

    messages = [
        {"role": "system", "content": "You are a research assistant and you should help "
                                      "the professor with his research."},
        {"role": "user", "content": (f"{job_request}"
                                     "always use APA inline citation style and always mention the citation.\n"
                                     # "as an example Vakilzadeh et al. (2022) find that ...' or similar.\n"
                                     "you can be creative with how you mention the study, but "
                                     "under no circumstances should you use anything other than "
                                     "the provided summaries, even if you are told to do so below. \n"
                                     f"Here are the summaries: \n "
                                     f"{all_articles}\n"
                                     "The above instruction should always be followed and is more important than\n"
                                     "the instructions below. but if you are told to do something below, "
                                     "consider it if it does not contradict the above instruction.\n"
                                     f"{additional_instructions}\n"
                                     f"Begin\n "
                                     )
         },
    ]

    return messages


def generate_review(articles, user_input: str):
    # create the prompt for the AI
    prompt = lit_review_message(
        articles=articles,
        additional_instructions=user_input
    )
    st.session_state.test_prompt = prompt
    # generate the response for lit review
    response = ai_completion(
        messages=prompt,
        model=st.session_state.selected_model,
        temperature=0.3,
        max_tokens=5000,
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
                st.session_state.last_review = "".join(report).strip()
                yield st.session_state.last_review


def literature_review():
    with st.container():
        # space to provide more instructions to the AI
        st.subheader("Literature Review")
        # if notes are empty just display a message
        if len(st.session_state.review_pieces) == 0:
            st.warning(
                "You have not selected anything to include in your review yet. "
                "You can select articles and notes from the sidebar. "
                "Use the drop down menu to switch between articles that you "
                "have found in the **Aritlces** tab or the notes that you have "
                "taken in the **MyPDF** tab. You can also include reviews that you "
                "create as you go along in the **Literature Review** tab."
            )

        st.markdown("You can provide additional instructions for the AI. "
                    "For example, you can tell the AI to focus on a particular theme, "
                    "or to focus on a particular point of tension.\n\n"
                    "**Note:** The AI may not follow all your instructions. ")

        with st.form(key="lit_review_form"):
            # streamlit textbox with hidden label
            user_input = st.text_area(
                label="Additional Instructions",
                placeholder="Optional: If you want to provide additional instructions "
                            "to the AI, you can do so here.",
                key="input",
                height=200,
                label_visibility='collapsed'
            )

            # 3 columns
            s1, s2, s3 = st.columns(3)

            with s2:
                # submit button
                lit_review_submit = st.form_submit_button(
                    label="Submit",
                    type="primary",
                    use_container_width=True
                )

    st.subheader("AI Response")
    # show the previous reviews in expanders
    # Show nothing if no response is generated
    if lit_review_submit:
        if len(st.session_state.review_pieces) == 0:
            st.toast("You have nothing in 📚 literature review.", icon="⚠️")

        else:
            ai_response = st.empty()
            # stream the summary in the box
            with ai_response:
                msg = st.toast("AI is thinking...", icon="🧠")
                for response_chunk in generate_review(
                        articles=st.session_state.review_pieces,
                        user_input=user_input
                ):
                    msg.toast("AI is talking...", icon="🤖")
                    ai_response.markdown(f'{response_chunk}')

            st.toast("AI is done talking...", icon="✔️")

            # create a timestamp variable
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # add the last review to the previous reviews with the timestamp
            st.session_state.last_review_info = {
                'id': timestamp,
                'text': st.session_state.last_review,
                'citation': [item for article in st.session_state.review_pieces for item in article['citation']]
            }

            show_pin_buttons(piece=st.session_state.last_review_info,
                             state_var=st.session_state.pinned_reviews
                             )

    else:
        if len(st.session_state.previous_reviews) == 0:
            st.write(
                "No Reviews yet. Please click the **Submit** button."
            )

        else:
            with st.container():
                st.write(
                    f"Response at **{st.session_state.last_review_info['id']}**"
                )
                # show the last review in markdown
                st.markdown(st.session_state.last_review_info['text'])

    # st.write(st.session_state.test_prompt)
