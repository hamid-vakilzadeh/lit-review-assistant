import os
import streamlit as st
import chromadb
from chromadb.utils import embedding_functions


openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    model_name="text-embedding-ada-002"
)

api = chromadb.PersistentClient(path="library")
collection = api.get_collection("langchain", embedding_function=openai_ef)


# TODO: Check the DOI for year = 0

@st.cache_data(show_spinner='searching for relevant articles...')
def find_docs(
        topic: str,
        year_range: list[int] = None,
        journal: list[str] = None,
        contains: list[str] = None,
        condition: str = None,
        number_of_docs: int = 10,
) -> list:
    # find documents related to the topic
    year_cond = {"$and": [
        {"year": {"$gte": year_range[0]}},
        {"year": {"$lte": year_range[1]}}
    ]}

    if not journal:
        where = year_cond

    elif len(journal) == 1:
        where = {"$and": [
            journal[0],
            year_cond
        ]
        }
    else:
        where = {"$and": [
            {"$or": journal,
             },
            year_cond
        ]
        }

    where_document = None

    if contains and len(contains) == 1:
        where_document = {"$contains": contains[0]}
    elif contains:
        contains_items = []
        for item in contains:
            contains_items.append({"$contains": item})
        if condition == "AND":
            where_document = {"$and": contains_items}
        elif condition == "OR":
            where_document = {"$or": contains_items}
        elif not condition:
            where_document = {"$and": contains_items}

    docs = collection.query(
        query_texts=topic,
        where=where,
        where_document=where_document,
        n_results=number_of_docs,
    )

    results = []
    for i in range(len(docs['ids'][0])):
        this_doc = {'doc': docs['documents'][0][i],
                    'year': docs['metadatas'][0][i]['year'],
                    'cite_counts': docs['metadatas'][0][i]['cite_counts'],
                    'title': docs['metadatas'][0][i]['title'],
                    'journal': docs['metadatas'][0][i]['journal'],
                    'doi': docs['metadatas'][0][i]['doi'],
                    'id': docs['ids'][0][i],
                    'distance': docs['distances'][0][i]
                    }
        results.append(this_doc)
    return results
