import streamlit as st
from utils.ai import ai_completion
from utils.funcs import set_command_none, set_command_search, set_command_pdf, pin_piece
import json
from tabs import article_search, pdf_search, sidebar
import time

from utils.firestore_db import (
    get_user_messages_ref,
    delete_document,
    get_document,
    get_all_messages,
    update_chat,
    add_new_message,
    update_chat_db
)


def change_chat():
    st.session_state.pop('messages_to_interface', None)
    st.session_state.pop('all_messages', None)
    st.session_state.pop('messages_to_interface_context', None)
    st.session_state.pop('messages_to_api', None)
    st.session_state.pop('messages_to_api_context', None)
    st.session_state.pop('pinned_articles', None)
    st.session_state.pop('pinned_pdfs', None)
    st.session_state.pop('review_pieces', None)
    st.session_state.pop('last_review', None)


def clear_chat():
    st.session_state.pop('chat_id', None)
    change_chat()


def delete_and_clear():
    delete_document(
        messages_ref=st.session_state.messages_ref,
        message_id=st.session_state.chat_id,
    )
    clear_chat()
    # user = st.session_state.user
    # st.session_state.clear()
    # st.session_state.user = user
    set_command_none()


def chat_response(
        instructions: str,
        context: list,
):
    if len(st.session_state.review_pieces) == 0:
        messages = [
            {"role": "system", "content": "Your job is to guide the user to provide you with context. "
             },
            {"role": "user", "content": (
                "If you are seeing this message, it means that the context is empty and the user has failed "
                "to provide you the necessary information. "
                "Tell them this message word by word with the markdown you see: \n"
                "You need to provide me some context before I can help you. "
                "You can use the :green[**search**] feature to find articles. "
                "You can also use the :green[**pdf**] feature to upload your PDFs. "
                "I recommend that you watch the video in the **About** tab or "
                "at the URL: https://www.youtube.com/watch?v=-93awViey4o. "

            )
             }]
        try:
            response = ai_completion(
                messages=messages,
                model=st.session_state.selected_model,
                temperature=0.1,  # st.session_state.temperature,
                # max_tokens=1000,
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
        except Exception as e:
            st.error(f"The AI is not responding. Please try again or choose another model.")
            st.stop()
        return

    if context:
        this_context = '\n '.join(context)
    else:
        this_context = 'no context'

    job_request = 'You are a research assistant and you should help ' \
                  'the professor with his research. ' \
                  'Your job is to identify themes and write a coherent literature review. ' \
                  'You are encouraged to identify points of tension.\n'

    st.session_state.messages_to_api.append(
        {"role": "user", "content": (
            f"{job_request}"
            f"the user said:\n "
            f"<instructions> {instructions} <instructions>\n "
            f"and provided the following context:\n "
            f"<context> {this_context} <context>\n "
            f"If there is no context see if the instructions are applicable to previous chat. "
            f"If the chat and context are both not research related, just say you can't help. "
            f"Follow the instructions only in the context of your persona. "
            f"You should NEVER use any studies that are not in the context or previous chats, "
            f"just say you can't help. "
            f"NEVER EVER use solely your own knowledge to answer questions. "
            "Always use APA inline citation style and always mention the citation.\n "
            "You can be creative with how you mention the study, but "
            "the above instruction should always be followed. "
            "If you are told to do something, "
            "consider it only if it does not contradict your persona and this instruction.\n"
            "Begin\n "
        )
         },
    )
    try:
        response = ai_completion(
            messages=st.session_state.messages_to_api,
            model=st.session_state.selected_model,
            temperature=0.3,  # st.session_state.temperature,
            # max_tokens=4000,
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
    except Exception as e:
        st.error(f"The AI is not responding. Please try again or choose another model.")
        st.stop()


def set_chat_name():
    st.session_state.change_name = True


def update_chat_name():
    st.session_state.current_chat_name = st.session_state.new_chat_name
    st.session_state.pop('change_name', None)
    update_chat_db(
        messages_ref=st.session_state.messages_ref,
        chat_id=st.session_state.chat_id,
        chat_name=st.session_state.current_chat_name,
        last_updated=time.time(),
    )
    st.session_state.all_messages = get_all_messages(st.session_state.messages_ref)


def create_new_chat():
    add_new_message(
        st.session_state.messages_ref,
        last_updated=time.time()
    )
    clear_chat()


def chat_name():
    if st.session_state.change_name:
        with st.form(key='change_chat_name'):
            name, change_button = st.columns([4, 1])
            name.text_input(
                label="Chat Name",
                placeholder="Chat Name",
                key="new_chat_name",
                value=st.session_state.current_chat_name,
                label_visibility="collapsed",
            )
            change_button.form_submit_button(
                label="Save",
                use_container_width=True,
                type='primary',
                on_click=lambda: update_chat_name(),
            )
    else:
        name, edit_button, delete_chat, new_chat = st.columns([4, 1, 1, 1])
        name.subheader(st.session_state.current_chat_name)
        # change chat name
        edit_button.button(
            label="Edit",
            key="edit_name",
            use_container_width=True,
            type='primary',
            on_click=lambda: set_chat_name(),
        )
        # clear chat button
        delete_chat.button(
            label="Delete",
            key="delete_chat",
            use_container_width=True,
            type='secondary',
            on_click=lambda: delete_and_clear(),
        )

        new_chat.button(
            label="New",
            key="new_chat",
            use_container_width=True,
            type='primary',
            on_click=lambda: create_new_chat(),
        )

        # show last updated in time formatted as 2021-01-01 00:00:00
        last_updated = st.session_state.all_messages[st.session_state.chat_id]['last_updated']
        st.caption(f"last updated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_updated))}")


def new_interface():
    # st.write(st.session_state)
    if "messages_ref" not in st.session_state:
        st.session_state.messages_ref = get_user_messages_ref(
            st.session_state.db, st.session_state.user['localId']
        )
    if 'all_messages' not in st.session_state:
        st.session_state.all_messages = get_all_messages(st.session_state.messages_ref)

    if len(st.session_state.all_messages) == 0:
        add_new_message(
            last_updated=time.time(),
            messages_ref=st.session_state.messages_ref,
        )
        st.session_state.all_messages = get_all_messages(st.session_state.messages_ref)

    with st.sidebar:
        st.selectbox(
            label="Chat History",
            key="chat_id",
            index=0,
            placeholder="Open a Chat",
            options=st.session_state.all_messages.keys(),
            format_func=lambda x: st.session_state.all_messages[x]['chat_name'],
            on_change=lambda: change_chat(),
        )
        # st.write(st.session_state.chat_id)
        st.session_state.current_chat_name = st.session_state.all_messages[st.session_state.chat_id]['chat_name']

        search_column, pdf_column, chat_return = st.columns(3)
        search_column.button(
            label="Search",
            key="search_command",
            use_container_width=True,
            type='secondary',
            on_click=lambda: set_command_search(),
        )
        pdf_column.button(
            label="PDF",
            key="pdf_command",
            use_container_width=True,
            type='secondary',
            on_click=lambda: set_command_pdf(),
        )
        chat_return.button(
            label="Chat",
            key="return_command",
            use_container_width=True,
            type='secondary',
            on_click=lambda: set_command_none(),
        )

    if "messages_to_interface" not in st.session_state:
        try:
            cloud_content = get_document(
                st.session_state.messages_ref, st.session_state.chat_id)
            if 'chat' in cloud_content:
                st.session_state.messages_to_interface = cloud_content['chat']
            else:
                st.session_state.messages_to_interface = []
            if 'pdfs' in cloud_content:
                # st.session_state.pinned_pdfs = cloud_content['pdfs']
                for pdf in cloud_content['pdfs']:
                    pin_piece(
                        pdf, st.session_state.pinned_pdfs
                    )
            else:
                st.session_state.pinned_pdfs = []
            if 'articles' in cloud_content:
                # st.session_state.pinned_articles = cloud_content['articles']
                for article in cloud_content['articles']:
                    pin_piece(
                        article, st.session_state.pinned_articles
                    )
            else:
                st.session_state.pinned_articles = []
            # st.session_state.review_pieces += st.session_state.pinned_pdfs
            # st.session_state.review_pieces += st.session_state.pinned_articles
            st.session_state.messages_to_api = st.session_state.messages_to_interface.copy()

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
                               "Start with **\\search** or **\\pdf** to begin. \n\n Alternatively, you can "
                               "click on the buttons on the left to start."},
            ]

    with st.sidebar:
        sidebar.show_sidebar()

    if 'command' not in st.session_state:
        st.session_state.command = None

    if st.session_state.command is None:
        chat_name()

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
            context = "\n\n ".join(st.session_state.messages_to_interface_context)
            st.session_state.messages_to_interface.append({"role": "user", "content": context + "\n\n" + user_input})
            # st.session_state.messages_to_api.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                with st.expander("Context"):
                    for item in st.session_state.messages_to_interface_context:
                        st.markdown(item)

                st.markdown(user_input)

            with st.chat_message("assistant"):
                ai_response = st.empty()

                msg = st.toast("AI is thinking...", icon="🧠")
                for response_chunk in chat_response(
                        instructions=user_input,
                        context=st.session_state.messages_to_api_context,
                ):
                    msg.toast("AI is talking...", icon="🤖")
                    ai_response.markdown(f'{response_chunk}')

            st.session_state.messages_to_interface.append({"role": "assistant", "content": response_chunk})
            st.session_state.messages_to_api.append({"role": "assistant", "content": response_chunk})

            update_chat(
                _db=st.session_state.db,
                username=st.session_state.user['localId'],
                chat_id=st.session_state.chat_id,
                chat_name=st.session_state.current_chat_name,
                last_updated=time.time(),
                messages_ref=st.session_state.messages_ref,
                message_content=st.session_state.messages_to_interface,
                pinned_articles=st.session_state.pinned_articles,
                pinned_pdfs=st.session_state.pinned_pdfs,
            )

    if st.session_state.command == "\\search":
        # if st.session_state.messages_to_interface[-1]['content'] != "\\search" and user_input:
        #     st.session_state.messages_to_interface.append({"role": "user", "content": user_input})
        article_search.article_search()

    elif st.session_state.command == "\\pdf":
        # if st.session_state.messages_to_interface[-1]['content'] != "\\pdf" and user_input:
        #     st.session_state.messages_to_interface.append({"role": "user", "content": user_input})
        pdf_search.pdf_search()

# st.write(st.session_state.messages_to_api_context)
