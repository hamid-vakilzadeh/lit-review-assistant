import os
import toml
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import streamlit as st
from typing import Optional, Dict


# os.environ["OPENAI_API_KEY"] = st.secrets['openai']
# conn = psycopg2.connect(database="hamid", user="postgres")
# cur = conn.cursor()  # cursor to execute SQL commands

# load the language model we're going to use to control the agent.
chat = ChatOpenAI(temperature=0)

# for retrieving documents from the database
embeddings = OpenAIEmbeddings()
db = Chroma(persist_directory='library/aaa/aaa-db2',
            embedding_function=embeddings)


@st.cache_data(show_spinner='searching for relevant articles...')
def find_docs(
        topic: str,
        include_only: Optional[Dict[str, str]] = None,
        number_of_docs: int = 10, ) -> list:
    # find documents related to the topic
    docs = db.similarity_search_with_score(
        query=topic,
        k=number_of_docs,
        )

    results = []
    for doc in docs:
        this_doc = {'doc': doc,
                    'year': int(doc[0].metadata['year']),
                    'cite_counts': int(doc[0].metadata['cite_counts'])
                    }
        results.append(this_doc)
    return results


# docs[0][0].page_content
# docs[0][0].metadata['source']


'''
@st.cache_data
def get_summary(articles: list[tuple]):
    # get the summary of the article from sql database and return it
    papers = [i[0].metadata["source"] for i in articles]
    placeholders = ', '.join(['%s' for item in papers])

    # papers = pd.DataFrame([i[0].metadata['source'] for i in articles], columns=['citation'])
    query = f"SELECT * FROM articles WHERE citation IN ({placeholders})"
    cur.execute(query, papers)

    rows = cur.fetchall()

    # Get the column names from the cursor description
    column_names = [desc[0] for desc in cur.description]

    # Convert the list of tuples into a list of dictionaries
    dict_rows = [dict(zip(column_names, row)) for row in rows]

    return dict_rows
'''