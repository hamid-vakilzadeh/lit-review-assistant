import streamlit as st
import time
from typing import Dict, List, Any


def initialize_local_storage():
    """Initialize local storage session state variables"""
    if 'local_chat_history' not in st.session_state:
        st.session_state.local_chat_history = {}
    
    if 'current_chat_id' not in st.session_state:
        st.session_state.current_chat_id = None
    
    if 'chat_counter' not in st.session_state:
        st.session_state.chat_counter = 0


def create_new_chat(chat_name: str = "Untitled") -> str:
    """Create a new chat and return its ID"""
    initialize_local_storage()
    
    chat_id = f"chat_{st.session_state.chat_counter}"
    st.session_state.chat_counter += 1
    
    st.session_state.local_chat_history[chat_id] = {
        'chat_name': chat_name,
        'last_updated': time.time(),
        'chat': [],
        'articles': [],
        'pdfs': []
    }
    
    return chat_id


def get_all_chats() -> Dict[str, Dict[str, Any]]:
    """Get all chat histories sorted by last updated"""
    initialize_local_storage()
    
    if not st.session_state.local_chat_history:
        # Create a default chat if none exists
        chat_id = create_new_chat()
        st.session_state.current_chat_id = chat_id
    
    # Sort by last_updated in descending order
    sorted_chats = {
        k: v for k, v in sorted(
            st.session_state.local_chat_history.items(),
            key=lambda item: item[1]['last_updated'],
            reverse=True
        )
    }
    
    return sorted_chats


def get_chat(chat_id: str) -> Dict[str, Any]:
    """Get a specific chat by ID"""
    initialize_local_storage()
    
    if chat_id in st.session_state.local_chat_history:
        return st.session_state.local_chat_history[chat_id]
    else:
        # Return empty chat structure if not found
        return {
            'chat_name': 'Untitled',
            'last_updated': time.time(),
            'chat': [],
            'articles': [],
            'pdfs': []
        }


def update_chat(
    chat_id: str,
    chat_name: str = None,
    message_content: List = None,
    pinned_articles: List = None,
    pinned_pdfs: List = None
):
    """Update a chat with new content"""
    initialize_local_storage()
    
    if chat_id not in st.session_state.local_chat_history:
        st.session_state.local_chat_history[chat_id] = {
            'chat_name': 'Untitled',
            'last_updated': time.time(),
            'chat': [],
            'articles': [],
            'pdfs': []
        }
    
    chat = st.session_state.local_chat_history[chat_id]
    
    if chat_name is not None:
        chat['chat_name'] = chat_name
    
    if message_content is not None:
        chat['chat'] = message_content
    
    if pinned_articles is not None:
        chat['articles'] = pinned_articles
    
    if pinned_pdfs is not None:
        chat['pdfs'] = pinned_pdfs
    
    chat['last_updated'] = time.time()


def delete_chat(chat_id: str):
    """Delete a chat by ID"""
    initialize_local_storage()
    
    if chat_id in st.session_state.local_chat_history:
        del st.session_state.local_chat_history[chat_id]


def clear_chat_messages(chat_id: str):
    """Clear messages from a chat but keep metadata"""
    initialize_local_storage()
    
    if chat_id in st.session_state.local_chat_history:
        st.session_state.local_chat_history[chat_id]['chat'] = []
        st.session_state.local_chat_history[chat_id]['last_updated'] = time.time()


def get_chat_messages_ref():
    """Return a mock messages reference for compatibility"""
    return None


def add_new_message(last_updated: float, chat_name: str = "Untitled", **kwargs):
    """Add a new message/chat - compatibility function"""
    chat_id = create_new_chat(chat_name)
    st.session_state.current_chat_id = chat_id
    return chat_id
