import streamlit as st
from utils.doi import get_article_with_doi

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
from chromadb.utils import embedding_functions


openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    model_name="text-embedding-ada-002",
    api_key=st.secrets["OPENAI_API_KEY"],
)

# Initialize ChromaDB client and collection
@st.cache_resource
def get_document_collection():
    """Get or create the document collection"""
    try:
        api = chromadb.PersistentClient(path="library")
        collection = api.get_or_create_collection("langchain", embedding_function=openai_ef)
        return collection
    except Exception as e:
        st.warning(f"Could not initialize persistent client, using in-memory: {e}")
        api = chromadb.Client()
        collection = api.get_or_create_collection("langchain", embedding_function=openai_ef)
        return collection

# Get the collection instance
collection = get_document_collection()


def found_articles_in_format(docs: dict) -> list:
    results = []
    for i in range(len(docs['ids'][0])):
        this_doc = {'text': docs['documents'][0][i].replace(docs['metadatas'][0][i]['authors'], ""),
                    'year': docs['metadatas'][0][i]['year'],
                    'cite_counts': docs['metadatas'][0][i]['cite_counts'],
                    'title': docs['metadatas'][0][i]['title'],
                    'journal': docs['metadatas'][0][i]['journal'],
                    'doi': docs['metadatas'][0][i]['doi'],
                    'id': docs['ids'][0][i],
                    'authors': docs['metadatas'][0][i]['authors'],
                    # 'relevance': round((1 - round(docs['distances'][0][i], 2)) * 100),
                    'type': 'abstract'
                    }
        results.append(this_doc)

    return results


#@st.cache_data(show_spinner=False)
def find_docs(
        topic: str,
        year_range: list[int] = None,
        journal: list[str] = None,
        doi: str = None,
        contains: list[str] = None,
        condition: str = None,
        author: str = None,
        number_of_docs: int = 10,
) -> list:
    """
    Find documents in the database that match the given criteria.

    :param topic: The topic to search for.
    :param year_range: The range of years to search for.
    :param journal: The list of journals to include in the search.
    :param doi: The DOI to search for.
    :param contains: The list of exact words/phrases to search for in the document.
    :param condition: The condition to use when searching for the words (only AND/OR).
    :param author: The author to search for.
    :param number_of_docs: The number of documents to return.
    """
    if not doi:
        # always enforce year range
        year_cond = {"$and": [
            {"year": {"$gte": year_range[0]}},
            {"year": {"$lte": year_range[1]}}
        ]}

        # if no journal, just use year
        if not journal:
            where = year_cond

        # for only one journal
        elif len(journal) == 1:
            where = {"$and": [
                journal[0],
                year_cond
            ]
            }

        # for multiple journals
        else:
            where = {"$and": [
                {"$or": journal,
                 },
                year_cond
            ]
            }

        # author search
        if author:
            author_cond = {"$contains": author}

        # if no contains, just use None
        where_document = None

        # if not contains
        if not contains and author:
            where_document = author_cond

        # for only one criterion for contains
        if contains and len(contains) == 1:
            where_document = {"$contains": contains[0]}
            if author:
                where_document = {"$and": [where_document, author_cond]}

        # for multiple criteria for contains
        elif contains:
            contains_items = []
            for item in contains:
                contains_items.append({"$contains": item})
            if condition == "AND":
                where_document = {"$and": contains_items}
                if author:
                    where_document["$and"].append(author_cond)
            elif condition == "OR":
                where_document = {"$or": contains_items}
                if author:
                    where_document = {"$and": [where_document, author_cond]}
            elif not condition:
                where_document = {"$and": contains_items}
                if author:
                    where_document["$and"].append(author_cond)

        # query the database
        docs = collection.query(
            query_texts=topic,
            where=where,
            where_document=where_document,
            n_results=number_of_docs,
        )

        # return the results in the desired format
        return found_articles_in_format(docs)

    else:
        if '\n' in st.session_state.doi_search:
            doi = doi.split('\n')

            # ensure duplicates are removed
            doi = list(set([item.strip() for item in doi]))
        else:
            doi = [doi]

        where = {"doi": {"$in": doi}}
        topic = ' '

        # query the database
        docs = collection.query(
            query_texts=topic,
            where=where
        )

        if len(docs['documents'][0]) == 0:
            docs = []
            for d in doi:
                try:
                    docs.append(get_article_with_doi(d))
                except Exception as e:
                    st.toast(e)
            return docs
        else:
            return found_articles_in_format(docs)
