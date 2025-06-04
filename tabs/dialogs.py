import streamlit as st
from tabs import article_search, pdf_search


@st.dialog("Search", width='large')
def search_dialog():
    article_search.article_search()


@st.dialog("Advanced Search", width='large')
def advanced_search_dialog():
    article_search.advanced_search()


@st.dialog("📁 Upload PDF", width='large')
def pdf_dialog():
    pdf_search.pdf_search()


@st.dialog("🚧 Under Construction 🚧", width='large')
def temporary_dialog():
    st.markdown("🚧 **New and Exciting Changes are coming to AIRA... Stay Tuned.**")
