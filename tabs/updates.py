import streamlit as st


def updates():
    st.header("Change log")
    st.subheader("January 07, 2024")
    st.markdown(
        """
        - Allow batch uploading of DOIs to retrieve all articles at once.
        - Ability to save multiple chats.
        - Fixed a bug where the length of chat was limited to arbitrary number of characters.
        """
    )
    st.header("In the works")
    st.markdown(
        """
        - Larger Dataset of articles.
        - Fixing a bug where the PDF responses are not accurate.
        - Fixing a bug where the context is not updated when the user changes the chat.
        """
    )