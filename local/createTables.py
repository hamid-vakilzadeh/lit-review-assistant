import psycopg2
import streamlit as st

conn = psycopg2.connect(database="hamid", user="postgres")
cur = conn.cursor()


@st.cache_data
def get_journal_names():
    cur.execute("SELECT * FROM journals_new;")
    return cur.fetchall()


if __name__ == '__main__':
    # create articles table
    cur.execute("CREATE TABLE IF NOT EXISTS articles ("
                "id SERIAL PRIMARY KEY, "
                "aaa_id TEXT, "
                "url TEXT, "
                "doi TEXT, "
                "journal TEXT, "
                "volume TEXT, "
                "issue TEXT, "
                "page TEXT, "
                "title TEXT, "
                "abstract TEXT, "
                "pdf_only BOOLEAN, "
                "citation TEXT );")

    # create journals table
    cur.execute("CREATE TABLE IF NOT EXISTS journals (" 
                "journal_id SERIAL PRIMARY KEY, "
                "aaa_name TEXT NOT NULL, "
                "name TEXT NOT NULL,"
                "abbreviation TEXT );")

    # conn.commit()
