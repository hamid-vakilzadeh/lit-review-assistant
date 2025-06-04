import streamlit as st
from utils.ai import ai_completion
from utils.funcs import (
    set_command_none,
    pin_piece
)
from utils.session_state_vars import ensure_session_state_vars
import json
from tabs import sidebar
import time
from tabs.css import css_code

from utils.local_storage import (
    get_chat_messages_ref,
    delete_chat,
    get_chat,
    get_all_chats,
    update_chat,
    add_new_message,
    clear_chat_messages
)

css_code()
ensure_session_state_vars()


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


def clear_chat_only():
    clear_chat_messages(st.session_state.chat_id)
    clear_chat()


def delete_and_clear():
    delete_chat(st.session_state.chat_id)
    clear_chat()
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
    update_chat(
        chat_id=st.session_state.chat_id,
        chat_name=st.session_state.current_chat_name,
    )
    st.session_state.all_messages = get_all_chats()


def create_new_chat():
    chat_id = add_new_message(last_updated=time.time())
    st.session_state.current_chat_id = chat_id
    clear_chat()


def chat_name():
    # Simplified chat interface - no name editing, just clear functionality
    st.subheader("Research Chat")
    
    # Only keep the clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True, type='secondary'):
        clear_chat_only()


def new_interface():
    # Initialize local storage and get all chats
    if 'all_messages' not in st.session_state:
        st.session_state.all_messages = get_all_chats()

    if len(st.session_state.all_messages) == 0:
        chat_id = add_new_message(last_updated=time.time())
        st.session_state.all_messages = get_all_chats()

    # Automatically use the first (and only) chat - no selection needed
    if 'chat_id' not in st.session_state:
        st.session_state.chat_id = list(st.session_state.all_messages.keys())[0]
    
    st.session_state.current_chat_name = st.session_state.all_messages[st.session_state.chat_id]['chat_name']

    if "messages_to_interface" not in st.session_state:
        try:
            chat_content = get_chat(st.session_state.chat_id)
            if 'chat' in chat_content:
                st.session_state.messages_to_interface = chat_content['chat']
            else:
                st.session_state.messages_to_interface = []
            if 'pdfs' in chat_content:
                for pdf in chat_content['pdfs']:
                    pin_piece(pdf, st.session_state.pinned_pdfs)
            else:
                st.session_state.pinned_pdfs = []
            if 'articles' in chat_content:
                for article in chat_content['articles']:
                    pin_piece(article, st.session_state.pinned_articles)
            else:
                st.session_state.pinned_articles = []
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
                               },
            ]


    chat_name()

    sidebar.show_sidebar()
    sidebar.choose_model()
    if len(st.session_state.review_pieces) == 0:
        st.info("Add articles to your literature review by selecting them in the context.")
    else:
        st.success(f"Articles in context: {len(st.session_state.review_pieces)}")

    chat_box = st.container(height=500)
    with chat_box:
        for message in st.session_state.messages_to_interface:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    user_input = st.chat_input("Type a message...")

    if user_input:
        with chat_box:
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
            chat_id=st.session_state.chat_id,
            chat_name=st.session_state.current_chat_name,
            message_content=st.session_state.messages_to_interface,
            pinned_articles=st.session_state.pinned_articles,
            pinned_pdfs=st.session_state.pinned_pdfs,
        )


    # st.write(st.session_state)
