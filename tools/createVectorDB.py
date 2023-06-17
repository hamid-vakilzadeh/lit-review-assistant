import os
from tqdm import tqdm
import pandas as pd
from langchain.text_splitter import TokenTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma, Pinecone
from pathlib import Path
import toml
import psycopg2
from typing import Optional
import pinecone

aaa_library = 'library/aaa'

persist_directory = 'aaa-db2'
Path(aaa_library, persist_directory).mkdir(exist_ok=True, parents=True)

# read toml file
secrets = toml.load('.streamlit/secrets.toml')
os.environ["OPENAI_API_KEY"] = secrets['openai']

conn = psycopg2.connect(database="hamid", user="postgres")
cur = conn.cursor()


def chunk_docs(
        data: pd.DataFrame,
        abstract_column: Optional[str],
        chunk_size: int = 1000,
        reference_column: Optional[str] = None,
        doi_column: Optional[str] = None,
        journal_column: Optional[str] = None,
        year_column: Optional[str] = None,
        title_column: Optional[str] = None,
        cite_count_column: Optional[str] = None,
):
    text_splitter = TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=0)

    docs_agg = []
    for i in tqdm(range(len(data))):

        docs = text_splitter.create_documents([data.iloc[i][abstract_column]])
        for text in docs:
            if reference_column is not None:
                text.metadata['citation'] = data.iloc[i][reference_column]
            if doi_column is not None:
                text.metadata['doi'] = data.iloc[i][doi_column]
            if journal_column is not None:
                text.metadata['journal'] = data.iloc[i][journal_column]
            if year_column is not None:
                text.metadata['year'] = data.iloc[i][year_column]
            if title_column is not None:
                text.metadata['title'] = data.iloc[i][title_column]
            if cite_count_column is not None:
                text.metadata['cite_counts'] = data.iloc[i][cite_count_column]

            docs_agg += docs

    return docs_agg


if __name__ == '__main__':
    # create a vector database of the documents embeddings
    # get all abstracts
    all_abstracts = pd.read_sql_query("SELECT abstract, citation, doi, journal "
                                      "from articles where abstract is not null;", conn)

    docs_cited = chunk_docs(all_abstracts,
                            abstract_column='abstract',
                            citations_column='citation',
                            journal_column='journal',
                            doi_column='doi')

    # create a vector database of the documents embeddings using Chroma
    embeddings = OpenAIEmbeddings()
    vector_db = Chroma.from_documents(
        documents=docs_cited,
        embedding=embeddings,
        persist_directory=os.path.join(aaa_library, 'aaa-db'))
    vector_db.persist()

    # load the doi database from jsonlines
    articles_new = pd.read_json('temp/articles_new.jsonl', lines=True)
    # replace NA with None in year column
    articles_new['year'] = articles_new['year'].fillna(0)
    # convert all columns to string
    articles_new['year'] = articles_new['year'].astype(int).astype(str)
    articles_new['is-referenced-by-count'] = articles_new['is-referenced-by-count'].astype(int).astype(str)

    docs_cited = chunk_docs(articles_new,
                            abstract_column='abstract',
                            journal_column='journal',
                            doi_column='DOI',
                            title_column='title',
                            year_column='year',
                            cite_count_column='is-referenced-by-count')

    # create a vector database of the documents embeddings using Chroma
    embeddings = OpenAIEmbeddings()
    vector_db = Chroma.from_documents(
        documents=docs_cited,
        embedding=embeddings,
        persist_directory=os.path.join(aaa_library, 'aaa-db2'))
    vector_db.persist()

    # try pinecone
    test_sample = docs_cited[0:100]

    pinecone.init(
        api_key=secrets['pinecone_api'],  # find at app.pinecone.io
        environment=secrets['pinecone_env']  # next to api key in console
    )

    index_name = "lit-review-demo"

    # pineconeDB
    pinecone_db = Pinecone.from_documents(
        documents=test_sample,
        embedding=embeddings,
        index_name=index_name)
