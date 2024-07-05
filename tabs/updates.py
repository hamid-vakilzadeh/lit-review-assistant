import streamlit as st


def updates():
    st.header("Change log")
    st.subheader("July 4, 2024")
    st.markdown(
        """
        - A completely redesigned interface.
        - Added 3 new models for generating responses (Claude 3.5 Sonnet, Gemini Flash 1.5, Llama 3)
        - Happy 4th of July! 🎆🎇🎉
            
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

    st.subheader("May 14, 2024")
    st.markdown(
        """
        - GPT-4o is now available for generating responses.
        """
    )

    st.subheader("March 15, 2024")
    st.markdown(
        """
        - Google Gemini Pro model is now available for generating responses.
        """
    )

    st.subheader("January 31, 2024")
    st.markdown(
        """
        - The database now contains more than 60,000 articles from the top 25 journals ranked on [BYU Accounting Ranking](https://www.byuaccounting.net/tenure/journalsincluded.php)
        - Added "Clear All Pinned" button to the sidebar.
        - Added "Clear" Button for Chat (i.e. keep the pinned articles and clear the current chat).
        - Added "Feedback Page" to the sidebar (we collect your feedback for research purposes).
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
