import streamlit as st
from utils.doi import get_citation
from pypdf import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from utils.ai import ai_completion
from utils.funcs import show_pin_buttons
import json
import time
import chromadb
from utils.documentSearch import openai_ef

text_splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=2000,
    chunk_overlap=100
)


@st.cache_resource
def get_chromadb_running():
    memory_client = chromadb.Client()
    # memory_client.delete_collection("pdf")
    memory_collection = memory_client.get_or_create_collection(
        "pdf",
        embedding_function=openai_ef
    )
    return memory_collection


def pdf_quick_summary(
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
            - If you find other cited paper, you should attribute relevant part to relevant studies.
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


def pdf_q_and_a(
        question,
        citation,
        query,
) -> list:
    information = "\n".join([f"- {item}" for item in query['documents'][0]])

    messages = [
        {"role": "system",
         "content": "You are a researcher and you are collecting notes for your research paper."
         },
        {"role": "user", "content": (
            """
            The following paragraphs are originally from {citation}.

            You are writing a summary to answer the following question:

            {question}
            
            You should answer the questions based on the following information:
            
            {information}

            if the answer is not in the information provided, don't make stuff up. Just say I don't know or 
            I could not find the answer.
            
            ALWAYS use citations following these rules: 
            - Always start with the APA name and year of the paper and make it clear that you the
            - Do not use 'this paper' or similar phrases when referring to the current study. Otherwise you will be penalized.
            - If you find other cited paper, you should attribute relevant part to relevant studies.
            - Third, Any other paragraphs that have no citations should be attributed to authors of the current study. 

            Please don't provide a conclusion or closing remark, as you are only seeing part of the literature. 
            if you do not follow the above rules, you will be penalized.
            
            Use Latex for mathematical equations and symbols, by wrapping them in "$" or "$$" (the "$$" must be on their own lines).
            use proper formatting to emphasize, italicize or bold the text as necessary.

            Begin:
            """.format(question=question, citation=citation, information=information)

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
            text.metadata['part_number'] = docs.index(text)

        this_pdf += docs

    return {'texts': this_pdf, 'num_pages': len(file.pages)}


@st.cache_data(show_spinner="Reading the PDF...")
def add_docs_to_db(_fulltext, _doi_to_add, _pdf_collection):
    _pdf_collection.add(
        documents=[item.page_content for item in _fulltext],
        metadatas=[{'doi_id': _doi_to_add['doi_id'], **item.metadata} for item in _fulltext],
        ids=["-".join([_doi_to_add['doi_id'],
                       'page',
                       str(item.metadata['page_number']),
                       str(item.metadata['part_number'])]
                      ) for item in _fulltext]
    )


def pdf_search():
    pdf_collection = get_chromadb_running()

    st.subheader("PDF Article Search")

    with st.expander("PDF Import Box", expanded=True):
        st.write("In this section your can provide your own article in PDF format and"
                 "the AI assistant can help you get deeper insights into the article.")
        st.info(
            f"You can ask specific questions about any pdf you uploaded. "
            f"First, select the article you want to review and start with a "
            f"**Quick Summary**! or ask a question using the **Q&A** option."
        )
        dois_present = [d.get('doi', None) for d in st.session_state.pdf_history]

        # upload the pdf file
        with st.form(key='pdf_upload_form', clear_on_submit=True):
            uploaded_file = st.file_uploader(
                "Upload your PDF file",
                type=["pdf"],
                disabled=False,
                key='pdf_file_uploader',
            )

            # text box for entering the doi
            st.text_input(
                label="Enter the DOI of the article",
                placeholder="e.g.  https://doi.org/10.1111/j.1475-679X.2006.00214.x",
                max_chars=None,
                key='pdf_doi_input',
                type='default'
            ).strip()

            st.markdown("""
                PDF file and its DOI are both necessary for generating summaries.
                Please ensure that the provided DOI is for the selected paper. 
                **:red[ONLY THE ORIGINAL DOI IS VALID!]** Any other variations (e.g., 
                through university proxies) would not work.
                """)

            # 3 columns for submit button
            s1, s2, s3 = st.columns(3)
            # submit button
            with s2:
                pdf_form_submit = st.form_submit_button(
                    label='➕ **import my PDF**',
                    type='primary',
                    use_container_width=True,
                )

    if pdf_form_submit:
        if uploaded_file is None:
            st.error(
                f"Please upload a pdf file and enter the DOI of the article."
            )
        elif st.session_state.pdf_doi_input in dois_present:
            st.success(
                f"This article has already been uploaded. Please select it from the list below."
            )
        else:
            try:
                fulltext = get_pdf_text(uploaded_file)['texts']
                # create pdf object to save in the session state
                doi_to_add = {
                    'doi': st.session_state.pdf_doi_input,
                    'citation': get_citation(st.session_state.pdf_doi_input),
                    'intro': [page.page_content for page in fulltext[:2]],
                    'num_pages': get_pdf_text(uploaded_file)['num_pages'],
                    'id': int(time.time()),
                    'doi_id': ''.join(st.session_state.pdf_doi_input.split("/")[1:]),
                    'pieces': []
                }

                dois_present = [d['doi'] for d in st.session_state['pdf_history']]
                if doi_to_add not in dois_present:
                    st.session_state['pdf_history'].append(doi_to_add)

                # add docs to the chromadb
                add_docs_to_db(fulltext, doi_to_add, pdf_collection)

            except Exception as e:
                st.error(f"The DOI is invalid. Please check the DOI and try again.\n\n {e}")

            st.experimental_rerun()

    if len(dois_present) > 0:
        doi = st.selectbox(
            label="Select the article you want to review",
            options=dois_present,
            index=len(dois_present)-1,
            key='pdf_select_box'
        )

        citation_area = st.empty()

        if doi in dois_present:
            # get the text from the pdf
            st.session_state.current_pdf = [d for d in st.session_state.pdf_history if d.get('doi', None) == doi][0]

            # show the number of pages for the pdf
            # show the citation
            citation_area.markdown(f"**{st.session_state.current_pdf['citation'].strip()}**")

            # show radio button for quick summary or q&a
            st.radio(
                label="Select the type of summary you want",
                options=['Quick Summary', 'Q&A'],
                index=0,
                horizontal=True,
                key='pdf_summary_type'
            )

            if st.session_state.pdf_summary_type == 'Quick Summary':
                with st.form(key='pdf_qa_form', clear_on_submit=True):
                    # show a button to start the review
                    summarize_button = st.form_submit_button(
                        label="📝 **Quick Summary**",
                        use_container_width=True,
                        type='primary',
                        disabled=False
                    )

            elif st.session_state.pdf_summary_type == 'Q&A':
                with st.form(key='pdf_qa_form', clear_on_submit=True):
                    qa_col1, qa_col2 = st.columns([4, 1])
                    # show a text input for q&a
                    qa_col1.text_input(
                        label="Enter your question here",
                        placeholder="e.g. What is the main contribution of this paper?",
                        max_chars=None,
                        key='pdf_qa_input',
                        type='default',
                        label_visibility='collapsed'
                    ).strip()

                    # show a button to start the review
                    with qa_col2:
                        submit_question = st.form_submit_button(
                            label="🤨 **Ask**",
                            use_container_width=True,
                            type='primary',
                            disabled=False
                        )

            response_area = st.empty()

            # show a text area for the response
            if st.session_state.pdf_summary_type == 'Quick Summary':
                if summarize_button:
                    # extract the first two pages of the pdf

                    prompt = pdf_quick_summary(
                        document=st.session_state.current_pdf['intro'],
                        citation=st.session_state.current_pdf['citation']
                    )
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
                                st.session_state.last_pdf_response = "".join(report).strip()
                                response_area.markdown(f'{st.session_state.last_pdf_response}')

                    piece_info = dict(
                        id=int(time.time()),
                        citation=st.session_state.current_pdf['citation'],
                        doi_id=st.session_state.current_pdf['doi_id'],
                        doi=st.session_state.current_pdf['doi'],
                        type='summary',
                        prompt='summary',
                        text=st.session_state.last_pdf_response
                    )

                    st.warning(
                        f"When AI response appears, you can 📌 **pin** it by clicking on the pin button."
                        f"otherwise, the response will be lost."
                    )
                    show_pin_buttons(
                     piece=piece_info,
                     state_var=st.session_state.pinned_pdfs,
                     )

            elif st.session_state.pdf_summary_type == 'Q&A':
                if submit_question:
                    if st.session_state.pdf_qa_input != '':

                        query_results = pdf_collection.query(
                            query_texts=st.session_state.pdf_qa_input,
                            where={"doi_id": st.session_state.current_pdf['doi_id']},
                            n_results=3
                        )

                        prompt = pdf_q_and_a(
                            query=query_results,
                            question=st.session_state.pdf_qa_input,
                            citation=st.session_state.current_pdf['citation']
                        )

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
                                    st.session_state.last_pdf_response = "".join(report).strip()
                                    response_area.markdown(f'{st.session_state.last_pdf_response}')

                        piece_info = dict(
                            id=int(time.time()),
                            citation=st.session_state.current_pdf['citation'],
                            doi_id=st.session_state.current_pdf['doi_id'],
                            doi=st.session_state.current_pdf['doi'],
                            type='Q&A',
                            prompt=st.session_state.pdf_qa_input,
                            text=st.session_state.last_pdf_response
                        )

                        st.warning(
                            f"When AI response appears, you can 📌 **pin** it by clicking on the pin button."
                            f"otherwise, the response will be lost."
                        )

                        show_pin_buttons(
                            piece=piece_info,
                            state_var=st.session_state.pinned_pdfs,
                        )

        # st.write(st.session_state.pinned_pdfs)
