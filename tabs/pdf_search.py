import streamlit as st


def pdf_search():
    st.subheader("PDF Article Search")
    st.write("In this section your can provide your own article in PDF format and"
             "the AI assistant can help you get deeper insights into the article.")

    # upload the pdf file
    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"], disabled=True)
    st.write('**Note:** This feature is not yet available.')
