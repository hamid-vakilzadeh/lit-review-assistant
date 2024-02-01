import streamlit as st


def updates():
    st.header("Change log")
    st.subheader("January 31, 2024")
    st.markdown(
        """
        - The database now contains more than 60,000 articles from the top 25 journals ranked on [BYU Accounting Ranking](https://www.byuaccounting.net/tenure/journalsincluded.php)
        - Added "Clear All Pinned" button to the sidebar.
        - Added "Clear Chat" Button (i.e. keep the pinned articles and clear the current chat.
        - Added "Research Project Page" to the sidebar (we collect your feedback for research purposes).
        """
    )

    st.header("In the works")
    st.markdown(
        """
        - Larger Dataset of articles.
        - Enhanced article search capabilities.
        - Fixing a bug where the PDF responses are not accurate.
        - Fixing a bug where the context is not updated when the user changes the chat.
        """
    )

    st.subheader("January 07, 2024")
    st.markdown(
        """
        - Allow batch uploading of DOIs to retrieve all articles at once.
        - Ability to save multiple chats.
        - Fixed a bug where the length of chat was limited to arbitrary number of characters.
        """
    )
