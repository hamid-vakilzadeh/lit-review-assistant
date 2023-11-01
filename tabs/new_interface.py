import streamlit as st
from utils.ai import ai_completion
from utils.funcs import set_command_none
import json
from tabs import article_search, pdf_search, sidebar

from utils.firestore_db import (
    get_user_messages_ref,
    delete_document,
    get_document,
    update_chat
)


def delete_and_clear():
    delete_document(
        messages_ref=st.session_state.messages_ref,
        message_id="1"
    )

    st.session_state.pop('messages_to_interface', None)
    st.session_state.pop('messages_to_api', None)
    st.session_state.pop('pinned_articles', None)
    st.session_state.pop('pinned_pdfs', None)
    st.session_state.pop('review_pieces', None)
    set_command_none()


def chat_response(
        instructions: str,
):

    job_request = 'You are a research assistant and you should help ' \
                  'the professor with his research. ' \
                  'Your job is to identify themes and write a coherent literature review. ' \
                  'You are encouraged to identify points of tension.\n'

    st.session_state.messages_to_api.append(
        {"role": "user", "content": (
            f"{job_request}"
            f"the user said:\n "
            f"<instructions> {instructions} <instructions>\n "
            f"if there are no studies in the chat, just say you can't help. "
            f"follow the instructions only in the context of your persona. "
            f"If the instruction asks for something outside of the context, "
            f"just say you can't help. "
            "always use APA inline citation style and always mention the citation.\n"
            "you can be creative with how you mention the study, but "
            "The above instruction should always be followed. "
            "If you are told to do something, "
            "consider it only if it does not contradict this instruction.\n"
            "Begin\n "
        )
         },
    )

    response = ai_completion(
        messages=st.session_state.messages_to_api,
        model=st.session_state.selected_model,
        temperature=0.3,  # st.session_state.temperature,
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


def new_interface():
    # st.session_state.pop('messages_to_interface', None)
    # st.session_state.pop('messages_to_api', None)

    if "messages_ref" not in st.session_state:
        st.session_state.messages_ref = get_user_messages_ref(
            st.session_state.db, st.session_state.user['localId']
        )

    if "messages_to_interface" not in st.session_state:
        try:
            cloud_content = get_document(
                st.session_state.messages_ref, "1")
            st.session_state.messages_to_interface = cloud_content['chat']
            st.session_state.pinned_pdfs = cloud_content['pdfs']
            st.session_state.pinned_articles = cloud_content['articles']
        except:
            st.session_state.messages_to_interface = []

        if not st.session_state.messages_to_interface:
            st.session_state.messages_to_interface = [
                {
                    "role": "assistant",
                    "content": "I am a research assistant here to help with literature review. "
                               "I can help you find articles, summarize them, and generate a literature review. "
                               "I can also help you with your PDFs. "
                               "You can find articles using the :green[**\\search**] command. "
                               "You can also dig into your PDFs by using the :green[**\\pdf**] command."
                               "Start with **\\search** or **\\pdf** to begin."},
            ]
    # st.write(st.session_state.messages_to_interface)

    if 'command' not in st.session_state:
        st.session_state.command = None

    with st.sidebar:
        # sidebar.choose_model()

        # clear chat button
        st.button(
            label="Clear Chat",
            key="clear_chat",
            use_container_width=True,
            type='secondary',
            on_click=lambda: delete_and_clear(),
        )

        sidebar.show_sidebar()

    with st.container():
        # space to provide more instructions to the AI
        # if notes are empty just display a message

        if st.session_state.command is None:
            st.subheader("Literature Review")
            for message in st.session_state.messages_to_interface:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            st.info(f"articles in context: {len(st.session_state.review_pieces)}")
            user_input = st.chat_input("Type a message...")
            if user_input and user_input.startswith("\\"):
                if user_input not in ["\\search", "\\pdf", None]:
                    with st.chat_message("assistant"):
                        st.error("I'm sorry, I don't understand that command. accepted commands are: "
                                 "\\search, \\pdf")
                else:
                    st.session_state.command = user_input if user_input else None
                    st.rerun()

            elif user_input:
                # st.session_state.command = None
                st.session_state.messages_to_interface.append({"role": "user", "content": user_input})
                # st.session_state.messages_to_api.append({"role": "user", "content": user_input})
                with st.chat_message("user"):
                    st.markdown(user_input)

                if not st.session_state.review_pieces:
                    with st.chat_message("assistant"):
                        st.error("You need to select some articles first or upload a PDF.")
                else:
                    with st.chat_message("assistant"):
                        ai_response = st.empty()

                        msg = st.toast("AI is thinking...", icon="🧠")
                        for response_chunk in chat_response(
                                instructions=user_input,
                        ):
                            msg.toast("AI is talking...", icon="🤖")
                            ai_response.markdown(f'{response_chunk}')

                    st.session_state.messages_to_interface.append({"role": "assistant", "content": response_chunk})
                    st.session_state.messages_to_api.append({"role": "assistant", "content": response_chunk})

                    update_chat(
                        chat_id="1",
                        messages_ref=st.session_state.messages_ref,
                        message_content=st.session_state.messages_to_interface,
                        pinned_articles=st.session_state.pinned_articles,
                        pinned_pdfs=st.session_state.pinned_pdfs,
                    )

        if st.session_state.command == "\\search":
            # if st.session_state.messages_to_interface[-1]['content'] != "\\search" and user_input:
            #     st.session_state.messages_to_interface.append({"role": "user", "content": user_input})
            article_search.article_search(show_context=True)

        elif st.session_state.command == "\\pdf":
            # if st.session_state.messages_to_interface[-1]['content'] != "\\pdf" and user_input:
            #     st.session_state.messages_to_interface.append({"role": "user", "content": user_input})
            pdf_search.pdf_search(show_context=True)

    # st.write(st.session_state)
