from google.cloud import firestore
import streamlit as st


@st.cache_resource
def init_firestore_client(json_file):
    return firestore.Client.from_service_account_json(json_file)


def get_user_messages_ref(_db, username):
    user_ref = _db.collection("users").document(username)
    messages_ref = user_ref.collection('messages')
    return messages_ref


def get_all_messages(_messages_ref):
    all_messages = {}
    for doc in _messages_ref.stream():
        doc_id = doc.id
        chat = doc.to_dict()
        all_messages[doc_id] = chat
    sorted_history = {k: v for k, v in sorted(all_messages.items(), key=lambda item: item[0], reverse=True)}

    return sorted_history


def get_document(_messages_ref, message_id):
    document_ref = _messages_ref.document(message_id)
    document = document_ref.get()
    return document.to_dict()


def add_new_message(messages_ref, title, message_content):
    document_ref = messages_ref.document()
    document_ref.set(
        {
            'title': title
            ,
            "chat": message_content
        }
    )


def update_chat(messages_ref, chat_id, message_content):
    document_ref = messages_ref.document(chat_id)
    document_ref.set(
        {
            "chat": message_content
        },
        merge=True
    )


def delete_document(messages_ref, message_id):
    messages_ref.document(message_id).delete()
