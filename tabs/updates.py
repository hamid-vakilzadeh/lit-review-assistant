import streamlit as st


def updates():
    st.header("Change log")
    st.subheader("June 4, 2025")
    st.markdown(
        """
        **🎉 Major Interface Redesign & RAG Implementation**
        - **Complete UI Overhaul**: New intuitive three-column layout with streamlined research workflow
        - **Enhanced RAG-Powered PDF Processing**: Upload multiple PDFs with automatic text extraction, citation generation, and vector storage using ChromaDB
        - **Enhanced Context Management**: Real-time context status indicators, individual paper management, and persistent context across chat sessions
        - **Intelligent Content Retrieval**: Semantic search within uploaded PDFs using vector embeddings for more relevant AI responses
        - **Improved Research Workflow**: Direct integration between search, PDF upload, and context management with visual feedback
        - **Advanced PDF Capabilities**: Automatic citation extraction using AI, DOI integration, and first 500 words as abstracts
        - **Better AI Integration**: Enhanced prompting system with improved source attribution and critical analysis capabilities
        - **Multiple Document Support**: Upload and manage unlimited PDFs with efficient storage and retrieval
        """
    )
    st.subheader("July 30, 2024")
    st.markdown(
        """
        - A completely redesigned interface for easier navigation. 
        - AIRA now integrates with SemanticScholar. You can now search more 220 million papers.
        - The new search offers advanced search capabilities, including comprehensive results and detailed filtering. 
        """
    )
    st.header("In the works")
    st.markdown(
        """
        - In the near future users will be able to discover related 
        papers, access full texts, and explore author profiles to enhance their academic research. Stay Tuned.
        """
    )

    st.markdown("---")
    st.subheader("July 4, 2024")
    st.markdown(
        """
        - A completely redesigned interface.
        - Added 3 new models for generating responses (Claude 3.5 Sonnet, Gemini Flash 1.5, Llama 3)
        - Happy 4th of July! 🎆🎇🎉

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
