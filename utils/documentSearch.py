import streamlit as st

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
from chromadb.utils import embedding_functions


openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    model_name="text-embedding-ada-002"
)

api = chromadb.PersistentClient(path="library")
collection = api.get_collection("langchain", embedding_function=openai_ef)


# TODO: Check the DOI for year = 0

@st.cache_data(show_spinner=False)
def find_docs(
        topic: str,
        year_range: list[int] = None,
        journal: list[str] = None,
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
    :param contains: The list of exact words/phrases to search for in the document.
    :param condition: The condition to use when searching for the words (only AND/OR).
    :param number_of_docs: The number of documents to return.
    """

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
