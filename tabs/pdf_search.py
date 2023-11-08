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
from ast import literal_eval

text_splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=2000,
    chunk_overlap=100
)


@st.cache_resource
def get_chromadb_running():
    st.session_state.memory_client = chromadb.Client()
    # memory_client.delete_collection("pdf")
    st.session_state.memory_collection = st.session_state.memory_client.get_or_create_collection(
        "pdf",
        embedding_function=openai_ef
    )
    return st.session_state.memory_collection


def pdf_quick_summary(
        document,
        citation,
) -> list:
    messages = [
        {
            "role": "system",
            "content": "You are a research assistant and you should help the professor with their research. "
                       "You will be provided with documents in the chat and some requests. always refer to the context of the chat "
                       "for papers. Focus on the papers that the user provides as they change. Apologies are not necessary. "
                       "Your task is to answer the question using only the provided research articles and to cite the passage(s) "
                       "of the document used to answer the question in inline APA style. If the document does not contain the "
                       "information needed to answer this question then simply write: cannot answer based on the provided "
                       "documents. If an answer to the question is provided, it must be annotated with a citation. "
        },
        {"role": "user", "content": (
            """
            The following paragraphs are originally from <citation>{citation}<citation>.
            
            <context>{document}<context>

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
        {
            "role": "system",
            "content": "You are a research assistant and you should help the professor with their research. "
                       "You will be provided with documents in the chat and some requests. always refer to the context of the chat "
                       "for papers. Focus on the papers that the user provides as they change. Apologies are not necessary. "
                       "Your task is to answer the question using only the provided research articles and to cite the passage(s) "
                       "of the document used to answer the question in inline APA style. If the document does not contain the "
                       "information needed to answer this question then simply write: cannot answer based on the provided "
                       "documents. If an answer to the question is provided, it must be annotated with a citation. "
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


def get_citation_from_pdf(pdf) -> str:
    # combine the first two pages
    first_two_pages = " ".join([item.page_content for item in pdf['texts'][:2]])
    prompt = ("generate apa citation from this content which is from the first two pages of a pdf file in a python list where the first "
              "element is for the bibliography and the second item is for in-line citations, just give me a list and nothing else! Avoid "
              f"explaining yourself. : <content>{first_two_pages}<content>")
    try:
        response = ai_completion(
            messages=[{"role": "user", "content": prompt}],
            model='openai/gpt-4',
            temperature=0,  # st.session_state.temperature,
            max_tokens=300,
            stream=False,
        )
        citation_from_text = response.json()['choices'][0]['message']['content'].lower()
        # find the list in response based on the presence of []
        citation_from_text = citation_from_text[citation_from_text.find('['):citation_from_text.find(']')+1]
        # get citation from text as a list
        citation_from_text = literal_eval(citation_from_text)
        return citation_from_text
    except Exception as e:
        st.error(f"The AI is not responding. Please try again or choose another model.")
        st.stop()


@st.cache_data(show_spinner=False)
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
    if 'pdf_collection' not in st.session_state:
        st.session_state.pdf_collection = get_chromadb_running()

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
        uploaded_file = st.file_uploader(
            "Upload your PDF file",
            type=["pdf"],
            disabled=False,
            key='pdf_file_uploader',
        )

        st.radio(
            "I have the DOI of the article",
            options=['No', 'Yes'],
            key='pdf_doi_radio',
            horizontal=True
        )

        # 3 columns for submit button
        s1, s2 = st.columns([5, 1])
        # text box for entering the doi
        if st.session_state.pdf_doi_radio == 'Yes':
            st.session_state.pop('pdf_doi_input')
            s1.text_input(
                label="Enter the DOI of the article",
                placeholder="enter the DOI e.g.  https://doi.org/10.1111/j.1475-679X.2006.00214.x",
                max_chars=None,
                key='pdf_doi_input',
                type='default',
                label_visibility='collapsed'
            ).strip()

            st.markdown("""
                PDF file and its DOI are both necessary for generating summaries.
                Please ensure that the provided DOI is for the selected paper. 
                **:red[ONLY THE ORIGINAL DOI IS VALID!]** Any other variations (e.g., 
                through university proxies) would not work.
                """)
        else:
            st.session_state.pdf_doi_input = None

        # submit button
        with s2:
            pdf_form_import = st.button(
                label='**Import**',
                type='primary',
                use_container_width=True,
            )

        if pdf_form_import:
            if uploaded_file is None:
                st.toast(
                    f":red[**Please upload a pdf file and enter the DOI of the article.**]",
                    icon="⚠️",
                )

            elif st.session_state.pdf_doi_input in dois_present:
                st.toast(
                    f"**This article has already been imported!**", icon="😎"
                )
            else:
                try:
                    msg = st.toast(
                        f"**Importing the article. Please wait...**", icon="⌛"
                    )
                    fulltext = get_pdf_text(uploaded_file)['texts']
                    time.sleep(0.5)
                    msg.toast("**getting the citation...**", icon="📑")
                    if st.session_state.pdf_doi_input is None:
                        try:
                            citation = get_citation_from_pdf(get_pdf_text(uploaded_file))[0]
                            doi = get_citation_from_pdf(get_pdf_text(uploaded_file))[1]
                            if doi in dois_present:
                                st.toast(
                                    f"**This article has already been imported!**", icon="😎"
                                )
                                st.rerun()
                        except Exception as e:
                            st.error('Could not get citation from pdf. Please try again.')
                            st.stop()
                    else:
                        citation = get_citation(st.session_state.pdf_doi_input)
                        doi = st.session_state.pdf_doi_input
                    # create pdf object to save in the session state
                    doi_to_add = {
                        'doi': doi,
                        'citation': [citation],
                        'intro': [page.page_content for page in fulltext[:2]],
                        'num_pages': get_pdf_text(uploaded_file)['num_pages'],
                        'id': int(time.time()),
                        'doi_id': ''.join(doi.split("/")[1:]),
                        'pieces': []
                    }

                    if doi_to_add['doi_id'] == '':
                        doi_to_add['doi_id'] = doi_to_add['id']

                    msg.toast("**saving the article...**", icon="💾")

                    dois_present = [d['doi'] for d in st.session_state['pdf_history']]
                    if doi_to_add['doi'] not in dois_present:
                        st.session_state['pdf_history'].append(doi_to_add)

                        # add docs to the chromadb
                        add_docs_to_db(fulltext, doi_to_add, st.session_state.pdf_collection)

                    st.rerun()

                except Exception as e:
                    st.toast(f"**Invalid DOI. Please check the DOI and try again.**", icon="⛔️")

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
                # citation_area.markdown(f"**{st.session_state.current_pdf['citation'][0].strip()}**")
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
                        qa_col1, qa_col2 = st.columns([5, 1])
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
                            citation=st.session_state.current_pdf['citation'][0]
                        )
                        # response_area.write(text[0].page_content)

                        msg = st.toast("AI is thinking...", icon="🧠")
                        try:
                            response = ai_completion(
                                messages=prompt,
                                model=st.session_state.selected_model,
                                temperature=0.3,  # st.session_state.temperature,
                                max_tokens=3000,
                                stream=True,
                            )
                            collected_chunks = []
                            report = []
                            with response_area.container():
                                for line in response.iter_lines():
                                    msg.toast("AI is talking...", icon="🤖")
                                    if line and 'data' in line.decode('utf-8'):
                                        content = line.decode('utf-8').replace('data: ', '')
                                        if 'content' in content:
                                            message = json.loads(content, strict=False)
                                            collected_chunks.append(message)  # save the event response
                                            report.append(message['choices'][0]['delta']['content'])
                                            st.session_state.last_pdf_response = "".join(report).strip()
                                            response_area.markdown(f'{st.session_state.last_pdf_response}')

                            st.toast("AI is done talking...", icon="✔️")

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
                                f"If you like the response, 📌 **pin** it. "
                                f"Otherwise, the response will be lost."
                            )
                            show_pin_buttons(
                             piece=piece_info,
                             state_var=st.session_state.pinned_pdfs,
                             )
                        except Exception as e:
                            st.error(f"The AI is not responding. Please try again or choose another model.")
                            st.stop()

                elif st.session_state.pdf_summary_type == 'Q&A':
                    if submit_question:
                        if st.session_state.pdf_qa_input != '':

                            query_results = st.session_state.pdf_collection.query(
                                query_texts=st.session_state.pdf_qa_input,
                                where={"doi_id": st.session_state.current_pdf['doi_id']},
                                n_results=3
                            )

                            prompt = pdf_q_and_a(
                                query=query_results,
                                question=st.session_state.pdf_qa_input,
                                citation=st.session_state.current_pdf['citation']
                            )

                            msg = st.toast("AI is thinking...", icon="🧠")
                            try:
                                response = ai_completion(
                                    messages=prompt,
                                    model=st.session_state.selected_model,
                                    temperature=0.3,  # st.session_state.temperature,
                                    max_tokens=3000,
                                    stream=True,
                                )
                                collected_chunks = []
                                report = []
                                with response_area.container():
                                    for line in response.iter_lines():
                                        msg.toast("AI is talking...", icon="🤖")
                                        if line and 'data' in line.decode('utf-8'):
                                            content = line.decode('utf-8').replace('data: ', '')
                                            if 'content' in content:
                                                message = json.loads(content, strict=False)
                                                collected_chunks.append(message)  # save the event response
                                                report.append(message['choices'][0]['delta']['content'])
                                                st.session_state.last_pdf_response = "".join(report).strip()
                                                response_area.markdown(f'{st.session_state.last_pdf_response}')

                                st.toast("AI is done talking...", icon="✔️")

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
                                    f"If you like the response, 📌 **pin** it. "
                                    f"Otherwise, the response will be lost."
                                )

                                show_pin_buttons(
                                    piece=piece_info,
                                    state_var=st.session_state.pinned_pdfs,
                                )
                            except Exception as e:
                                st.error(f"The AI is not responding. Please try again or choose another model.")
                                st.stop()

    # st.write(st.session_state.current_pdf)


