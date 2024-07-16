import asyncio
from openai import AsyncOpenAI
import json
from openai import OpenAI
from cleantext.clean import clean
from pypdf import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from ast import literal_eval
import pandas as pd
from retry import retry
import chromadb.utils.embedding_functions as embedding_functions
import streamlit as st
import mdtex2html
from tenacity import retry as tr, wait_fixed, stop_after_attempt
from openai import APIConnectionError

from utils.firestore_db import get_user_messages_ref

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

text_splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=2000,
    chunk_overlap=100
)


# Define the summarizer function
@retry(tries=3, delay=2)
def agent(messages: list, max_tokens: int = 4096, json_format=False) -> str:
    response_type = None
    finish_reason = None
    if json_format:
        response_type = {"type": "json_object"}
    while finish_reason != 'stop':
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3,
            response_format=response_type,
            seed=1234

        )
        if response.choices[0].finish_reason == "stop":
            finish_reason = 'stop'

    return response.choices[0].message.content


openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=st.secrets['OPENAI_API_KEY'],
    model_name="text-embedding-3-small"
)


# Test the summarizer function
def messages_to_send_summarizer(page_content: str, part_number: int, total_parts: int):
    return [
        {"role": "system", "content": "You are a seasoned researcher with an eye for detail. You are skilled at uncovering the details of "
                                      "the of academic papers, and you are able to provide a comprehensive review of the paper to make it "
                                      "easy to replicate a study. Take as much notes as possible to help you remember the details of the "
                                      "paper. Your response should be in json format."
         },
        {"role": "user", "content": "You will be provided each page of a research paper along with predefined sections. "
                                    "Each predefined section also has a couple of example questions to help you identify what could be "
                                    "related to each section. Your task is to identify relevant pieces that are related to each section. "
                                    "Use only the section_names provided. don't make up your own section names."
                                    "Paraphrase the relevant pieces in your own words but make sure to include all the relevant information. "
                                    "Only return the relevant pieces in a json format with only the following keys: "
                                    "{'paper_info': None, "
                                    "'research_question': None, "
                                    "'research_design': None, "
                                    "'sample_selection': None, "
                                    "'measures_definition': None, "
                                    "'results': None, "
                                    "'limitation': None } "
                                    "for each section, if you find relevant information, put the information as the value like: "
                                    "{'section name goes here': 'relevant information goes here',} \n "
                                    "DO NOT USE ANY OTHER KEYS IN THE JSON. Do not include any additional information. "
                                    "if no relevant information found return: "
                                    "{'section name goes here': None} "
                                    "Sections with example questions: \n "
                                    "only use the predefined section names. "
                                    "* section name: paper_info: \n "
                                    "- What is the title of the paper? "
                                    "- Who are the authors? "
                                    "- What is the publication year? "
                                    "- What is the journal name? "
                                    "- What is the DOI? "
                                    "* section name: research_question \n "
                                    "- Identify the main question of the paper. "
                                    "- Identify the hypotheses of the paper. "
                                    "* section name: research_design \n "
                                    "- What is the main model?"
                                    "- What is the procedure to test the idea? "
                                    "* section name: sample_selection \n "
                                    "- What are the data sources? (e.g., Compustat, CRSP) "
                                    "- What is the sample creation process? "
                                    "- What is the sample period? "
                                    "- Are any industries excluded? "
                                    "* section name: measures_definition \n "
                                    "- What are the control variables? "
                                    "- What is the main X? "
                                    "- What is the main Y? "
                                    "- What are the names of the variables? "
                                    "- Is there any fixed effects in the regression model? "
                                    "- Are any variables replaced with zero if missing? "
                                    "- Are there any restriction (e.g., drop the negative values) on each variable? "
                                    "- Are the variables winsorized? "
                                    "* section name: results \n "
                                    "- What are the main results? "
                                    "- What are the additional/robustness tests? "
                                    "* section name: limitation \n "
                                    "- What are the limitations of the paper? "
         },
        {"role": "user", "content": f"page {part_number} of {total_parts}. "
                                    f"page_content: {page_content}"
         },
        {"role": "assistant", "content": f"My Answer: "},
    ]


# Test the summarizer function
def messages_to_send_organizer(section_contents: pd.DataFrame, section_name):
    messages = [
        {"role": "system", "content": "You are a seasoned research writer. You are skilled at notetaking on academic papers "
                                      "and put them in a coherent manner."
         },
    ]
    # iterate over test rows
    for index, row in section_contents.iterrows():
        messages.append(
            {"role": "assistant", "content": f"my notes for {section_name}:\n "
                                             f"note number {index + 1}: {str(row[section_name]).strip()} "}
        )

    messages += \
        [{"role": "user",
          "content": f"Your team member has recorded excerpts of a research paper related to {section_name}. "
                     f"Your task is to organize these pieces in a coherent manner and draft the {section_name} section of the final review. "
                     "Make sure to use the correct mathematical symbols and notations whenever needed. "
                     "Include everything in the notes and do not leave out any details but if there are duplicates "
                     "remove them. Your job is to organize the notes in a coherent manner with a great flow."
                     "so be smart and avoid any non-sense. "
                     "If you see the pronoun 'we' change it to 'the study'. "
                     "Do not add any additional comments. "
                     "Use proper grammar and punctuation. "
                     "Use proper markdown formatting. "
                     "When using Latex, make sure you use $ for inline math and $$ for block math. "

          },
         {
             "role": "assistant",
             "content": "Cleaned Notes: "
         }]

    return messages


def message_for_variables_list(summary_body: str):
    messages = [
        {"role": "system", "content": "You are an expert data analyst. You are skilled at identifying details of empirical analysis "
                                      "and can provide a complete list of the variables used in a study. Always return a list."
         },
        {"role": "user",
         "content": f"You have the summary of a research paper below: "
                    "Your task is to extract ALL the variables names. That is it! Nothing more nothing less. "
                    " return a list of variables names in the following format: "
                    "My Answer: ['variable name goes here', 'variable name goes here', ...] "
                    "Example: \n "
                    "My Answer: ['ROA', 'SIZE', 'LEV', 'MTB']"
                    f"<summary starts>{summary_body} <summary ends>. "
                    f"Make sure to include all the variables names."
                    f"Only Return a list with the format above and nothing else."
         },
        {
            "role": "assistant",
            "content": "My Answer: "
        }]

    return messages


def message_for_details_of_variables(summary_text: str, variables_list: str):
    messages = [
        {"role": "system", "content": "You are an expert data analyst. You are skilled at identifying details of empirical analysis "
                                      "and can provide a very detailed specifications of the variables used in a study."
                                      "Always return in json format."
         },
        {"role": "user",
         "content":
             f"You have the summary of a research paper below: "
             "Your task is to extract information about the variables of interest, "
             "along with detailed definitions, and any restrictions. "
             "Include everything in the notes and do not leave out any details. "
             " return a list of dictionaries with the following format: "
             "{'var_name': 'name goes here', 'restriction': 'restriction goes here', 'var_definition': 'definition goes here', 'var_requirements': 'requirements goes here'}, "
             "{'var_name': 'name goes here', 'restriction': 'restriction goes here', 'var_definition': 'definition goes here', 'var_requirements': 'requirements goes here'} "
             "Example: \n "
             "{'var_name': 'ROA', 'restriction': 'none', 'var_definition': 'Return on Assets', 'var_requirements': 'Net Income or loss and Total Assets'},"
             "{'var_name': 'SIZE', 'restriction': 'assets should not be negative', 'var_definition': 'log of total assets', 'var_requirements': 'Total Assets'} "
             f"<summary starts>{summary_text} <summary ends>."
             f"<variables of interest>{variables_list}</variables of interest>"
             f"Only Return a json with the format above and nothing else."
         # f"your response should be suitable for literal eval to read it as a list of dictionaries."
         },
        {
            "role": "assistant",
            "content": "My Answer: "
        }]

    return messages


def messages_for_research_designer(summary_text: str):
    messages = [
        {"role": "system", "content": "You are an expert research designer. You are skilled at identifying details of empirical analysis "
                                      "and can provide a very detailed instruction on how to replicate a study."
         },
        {"role": "user",
         "content":
             f"You have the summary of a research paper below: "
             "Your task is to lay out the step by step instructions on how to replicate the study. "
             "For example, what is the main empirical model? What are the variables in the model? "
             "What is the order of calculating the variables? "
             "Your steps should be small, granular, and detailed. "
             "Layout your instructions in a format like this:"
             "My Answer: \n"
             "Step 1: Do this "
             "Step 2: Then do that "
             "Step 3: After that do this other thing "
             "(Steps can continue n times)"
             f"<summary start>{summary_text}<summary end>"
         },
        {
            "role": "assistant",
            "content": "My Answer: \n"
        }]

    return messages


def get_pdf_text(file) -> dict:
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


def clean_text(input_text: str) -> str:
    return clean(
        input_text,
        fix_unicode=True,  # fix various unicode errors
        to_ascii=True,  # transliterate to closest ASCII representation
        lower=False,  # lowercase text
        no_line_breaks=False,  # fully strip line breaks as opposed to only normalizing them
        no_urls=True,  # replace all URLs with a special token
        no_emails=True,  # replace all email addresses with a special token
        no_phone_numbers=True,  # replace all phone numbers with a special token
        no_numbers=False,  # replace all numbers with a special token
        no_digits=False,  # replace all digits with a special token
        no_currency_symbols=False,  # replace all currency symbols with a special token
        no_punct=False,  # remove punctuations
        replace_with_url="<URL>",
        replace_with_email="<EMAIL>",
        replace_with_phone_number="<PHONE>",
        replace_with_number="<NUMBER>",
        replace_with_digit="0",
        replace_with_currency_symbol="<CUR>",
        lang="en"
    )


def convert_responses_to_df(responses: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(responses)
    df.reset_index(inplace=True)
    return df


@retry(tries=3, delay=2)
async def get_complete_review(df: pd.DataFrame) -> str:
    sections = ['paper_info', 'research_question', 'research_design', 'sample_selection', 'measures_definition', 'results', 'limitation']
    progress_text = "Putting the review together..."
    my_bar = st.progress(0, text=progress_text)

    section_messages = {}
    for section in sections:
        section_contents = df[['index', section]]
        section_contents.dropna(inplace=True)
        section_contents.reset_index(drop=True, inplace=True)
        messages = messages_to_send_organizer(section_contents, section)
        section_messages[section] = messages

    async def process_section(section):
        result = await make_call(section_messages[section], json_format=False)
        return section, result.replace('Cleaned Notes:', '')

    tasks = [process_section(section) for section in sections]

    results = []
    for i, task in enumerate(asyncio.as_completed(tasks)):
        section, result = await task
        results.append((section, result))
        my_bar.progress((i + 1) / len(sections), text="Putting the review together...")

    # Sort results based on the original order of sections
    results.sort(key=lambda x: sections.index(x[0]))
    whole_summary = "\n\n".join([result for _, result in results]).strip()

    my_bar.empty()
    return whole_summary


@retry(tries=3, delay=2)
def get_variables_names(summary_body: str) -> pd.DataFrame:
    messages = message_for_variables_list(summary_body)
    variable_definitions = agent(messages, json_format=False)
    list_of_vars = literal_eval(variable_definitions.replace(
        '```python', '').replace(
        '```', '').replace(
        'My Answer:', ''
    ))
    return pd.DataFrame(list_of_vars)


@retry(tries=3, delay=2)
def get_vars_definitions(vars: pd.DataFrame, summary_body) -> list:
    i = 0
    list_of_vars_definitions = []
    while i < len(vars):
        messages = message_for_details_of_variables(summary_body, vars.iloc[i:i + 5].to_markdown())
        variables_definitions = agent(messages)
        list_of_vars = variables_definitions.replace(
            '```python', '').replace(
            '```json', '').replace(
            'My Answer:', '').replace(
            '```', '')
        list_of_vars_definitions += json.loads(list_of_vars)
        i += 5
    return list_of_vars_definitions


aclient = AsyncOpenAI(
    # This is the default and can be omitted
    api_key=st.secrets["OPENAI_API_KEY"],
)


@tr(wait=wait_fixed(2), stop=stop_after_attempt(3),
    retry=(lambda retry_state: isinstance(retry_state.outcome.exception(), APIConnectionError)))
async def make_call(messages: list, max_tokens: int = 4096, json_format=False) -> str:
    response_type = None
    if json_format:
        response_type = {"type": "json_object"}
    try:
        response = await aclient.chat.completions.create(
            messages=messages,
            max_tokens=max_tokens,
            response_format=response_type,
            model="gpt-4o",
            temperature=0.3,
            seed=1234
        )
        return response.choices[0].message.content
    except APIConnectionError as e:
        print(f"Connection error: {e}")
        raise


def return_messages_as_literal(pieces: list[str]) -> list:
    literal_pieces = []
    for piece in pieces:
        try:
            response = literal_eval(piece.replace('My Answer:', '').replace('null', 'None'))
            literal_pieces.append(response)
        except:
            pass
    return literal_pieces


async def main(_docs):
    responses = []
    my_bar = st.progress(0, text=f"Starting to Reading the Paper...")

    tasks = [
        make_call(
            messages=messages_to_send_summarizer(
                page_content=clean_text(item.page_content),
                part_number=item.metadata['page_number'] + item.metadata['part_number'] + 1,
                total_parts=len(_docs['texts'])
            ),
            json_format=True
        )
        for item in _docs['texts']
    ]
    i = 1
    for task in asyncio.as_completed(tasks):
        percent_complete = i / len(_docs['texts'])
        summary = await task
        responses.append(summary)
        i += 1

        my_bar.progress(
            percent_complete,
            text=f"**{percent_complete * 100:.0f}%**"
        )

    my_bar.empty()
    return responses


def reviewer_ai():
    if "reviews_ref" not in st.session_state:
        st.session_state.messages_ref = get_user_messages_ref(
            st.session_state.db, st.session_state.user['localId'],
            collection_name="reviews"
        )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader('Reviewer AI')
        # st.session_state.pop('relevant_pieces_list', None)
        with st.form(
                key='form'
        ):
            st.write('Upload a PDF file to get a comprehensive review of the paper')
            st.file_uploader(
                label="Upload a file",
                type=['pdf'],
                accept_multiple_files=False,
                key='uploaded_file',
            )
            submitted = st.form_submit_button(
                label='Submit',
                on_click=lambda: st.session_state.pop('comprehensive_summary', None)
            )
        if submitted:
            # Load the PDF file
            st.session_state.text = get_pdf_text(st.session_state.uploaded_file)

            # get the relevant pieces

            st.session_state.relevant_pieces_list = asyncio.run(main(st.session_state.text))

            st.session_state.pop('text', None)

            # convert the responses to a dataframe
            st.session_state.relevant_pieces_df = convert_responses_to_df(
                return_messages_as_literal(st.session_state.relevant_pieces_list)
            )
            st.session_state.pop('relevant_pieces_list', None)

            # put together the summary:
            st.session_state.comprehensive_summary = asyncio.run(get_complete_review(st.session_state.relevant_pieces_df))
            st.session_state.pop('relevant_pieces_df', None)

        if 'comprehensive_summary' in st.session_state and 'uploaded_file' in st.session_state:
            col2.download_button(
                label="Download Review",
                data=mdtex2html.convert(st.session_state.comprehensive_summary),
                file_name=f'review_{st.session_state.uploaded_file.name.replace(".pdf", "")}.html',
                mime='text/markdown',
            )
