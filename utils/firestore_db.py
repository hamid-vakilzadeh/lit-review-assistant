import streamlit as st
import requests
import json


def create_new_profile(_db, username):
    user_ref = _db.collection("users").document(username)
    if not user_ref.get().exists:
        add_user_to_db(username, _db)

    if not user_ref.get().to_dict():
        st.session_state.profile_details = {
            'title': '',
            'first_name': '',
            'last_name': '',
            'position': '',
            'email': '',
        }
        user_ref.update(
            st.session_state.profile_details
        )

    else:
        st.session_state.profile_details = user_ref.get().to_dict()


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


def update_chat(messages_ref, chat_id, message_content, pinned_articles, pinned_pdfs):
    document_ref = messages_ref.document(chat_id)
    document_ref.set(
        {
            "chat": message_content
            ,
            "articles": pinned_articles
            ,
            "pdfs": pinned_pdfs
        },
        # merge=True
    )


def update_profile_db(username, _db, title, first_name, last_name, position, email):
    st.session_state.profile_details = {
        'title': title,
        'first_name': first_name,
        'last_name': last_name,
        'position': position,
        'email': email,
    }

    user_ref = _db.collection("users").document(username)
    user_ref.update(st.session_state.profile_details)


def delete_document(messages_ref, message_id):
    messages_ref.document(message_id).delete()


def update_password(id_token, new_password):
    pyrebaseConfig = json.loads(st.secrets["pyrebaseConfig"])
    api_key = pyrebaseConfig['apiKey']
    url = f'https://identitytoolkit.googleapis.com/v1/accounts:update?key={api_key}'

    headers = {
        'Content-Type': 'application/json'
    }

    data = {
        "idToken": id_token,
        "password": new_password,
        "returnSecureToken": True
    }

    response = requests.post(url, headers=headers, json=data)

    # Return the JSON response if you want
    return response.json()


def add_user_to_db(username, _db):
    user_ref = _db.collection("users")
    return user_ref.document(username).set({})


def new_user_request(username, _db):
    user_ref = _db.collection("new_user_requests")
    if not user_ref.get():
        user_ref.document(username).set({})
