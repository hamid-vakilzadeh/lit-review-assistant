import streamlit as st
from tools.doi import get_citation
from pypdf import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from tools.ai import ai_completion
import json

text_splitter = CharacterTextSplitter(chunk_size=3000, chunk_overlap=0)

# create a state to track the pdf summaries
if 'pdf_summaries' not in st.session_state:
    st.session_state.pdf_summaries = {}


def prep_gpt_review(
        document,
        citation,
) -> list:

    messages = [
        {"role": "system",
         "content": "You are a researcher and you are collecting notes for your literature review."
         },
        {"role": "user", "content": (
            """
            The following paragraphs are originally from {citation}.
        
            You are writing a paper, and you are taking notes about this paper. 
            Your job is to synthesize this paper. Try to make it concise and short.
        
            ALWAYS use citations following these rules: 
            - Always start with the APA name and year of the paper and make it clear that you talking about this paper
            - Do not use 'this paper' or similar phrases when referring to the current study. Otherwise you will be penalized.
            - Look for other studies mentioned in this paper. If you find other cited paper, you should attribute relevant part to relevant studies.
            - Third, Any other paragraphs that have no citations should be attributed to authors of the current study. 
        
            Please don't provide a conclusion or closing remark, as you are only seeing part of the literature. 
            if you do not follow the above rules, you will be penalized.
            
            Begin:
            {document}
            """.format(document=document, citation=citation)
                                     )
         },
    ]

    return messages


def get_pdf_text(file) -> []:
    file = PdfReader(file)

    # create a vector store
    this_pdf = []
    for page in range(len(file.pages)):

        this_page = file.pages[page].extract_text()
        docs = text_splitter.create_documents([this_page])
        for text in docs:
            text.metadata['page_number'] = page

        this_pdf += docs

    return this_pdf


def pdf_search():
    st.subheader("PDF Article Search")
    st.write("In this section your can provide your own article in PDF format and"
             "the AI assistant can help you get deeper insights into the article.")

    # upload the pdf file
    with st.form(key='pdf_analysis'):
        uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"], disabled=False)

        # text box for entering the doi
        doi = st.text_input(
            label="Enter the DOI of the article",
            value="",
            max_chars=None,
            key=None,
            type='default'
        ).strip()

        if doi in st.session_state.pdf_summaries.keys():
            submitted = st.form_submit_button(label='Regenerate Notes', type='secondary')
        else:
            submitted = st.form_submit_button(label='Take Notes', type='primary')

        if submitted:
            try:
                this_doi = get_citation(doi)
            except Exception as e:
                st.error(f"The DOI is invalid. Please check the DOI and try again.\n\n {e}")
                st.stop()

            text = get_pdf_text(uploaded_file)
            st.markdown(f"**{this_doi. strip()}**")
            response_area = st.empty()

            # extract the first two pages of the pdf
            intro = "".join([page.page_content for page in text[:2]])
            prompt = prep_gpt_review(document=intro, citation=this_doi)
            # response_area.write(text[0].page_content)

            with response_area.container():
                response = ai_completion(
                    messages=prompt,
                    model=st.session_state.selected_model,
                    temperature=st.session_state.temperature,
                    max_tokens=1500,
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
                        st.session_state.last_response = "".join(report).strip()
                        response_area.markdown(f'{st.session_state.last_response}')

            st.session_state.pdf_summaries[doi] = {
                'citation': this_doi,
                'summary': st.session_state.last_response
            }

            if st.session_state.selected_model == 'google/palm-2-chat-bison':
                st.experimental_rerun()

        elif doi in st.session_state.pdf_summaries.keys():
            st.markdown(f"**{st.session_state.pdf_summaries[doi]['citation'].strip()}**")
            st.markdown(f"{st.session_state.pdf_summaries[doi]['summary'].strip()}")

        else:
            st.info("Upload a PDF file and click the 'Take Notes' button to get started.")
