import pandas as pd
from bs4 import BeautifulSoup
import psycopg2

conn = psycopg2.connect(database="hamid", user="postgres")
cur = conn.cursor()


def get_year(x):
    try:
        return int(x['date-parts'][0][0])
    except TypeError:
        return None


if __name__ == '__main__':
    ####################################################################################################################
    # articles with abstract
    df = pd.read_json('temp/articles.jsonl', lines=True)
    df = df[df['abstract'].notna()]
    # use beautiful soup to remove html tags from abstract
    df['abstract'] = df['abstract'].apply(lambda x: BeautifulSoup(x, 'html.parser').find('jats:p').text)
    df['container-title'].value_counts()
    df['publisher'].value_counts()
    # get journal title from container-title
    df['journal'] = df['container-title'].apply(lambda x: x[0])

    # create a table for journals and set column values form counts of journals
    journals = pd.DataFrame(df['journal'].value_counts())
    journals.reset_index(inplace=True)

    journals['correct_name'] = journals['journal']
    journals['correct_name'].iloc[1] = 'Journal of Accounting, Auditing & Finance'
    journals['correct_name'].iloc[4] = 'Auditing: A Journal of Practice & Theory'
    journals['correct_name'].iloc[19] = 'Journal of Governmental & Nonprofit Accounting'
    journals['correct_name'].iloc[20] = 'Auditing: A Journal of Practice & Theory'
    journals['correct_name'].iloc[21] = 'Journal of the American Taxation Association'
    journals['correct_name'].iloc[22] = 'Auditing: A Journal of Practice & Theory'

    # join journals to df
    df = df.merge(journals, left_on='journal', right_on='journal', how='left')
    # drop journal column
    df.drop(columns=['journal', 'count'], inplace=True)

    # rename correct_name to journal
    df.rename(columns={'correct_name': 'journal'}, inplace=True)
    df.journal.value_counts()

    # create a table for journals and set column values form counts of journals
    journals = pd.DataFrame(df['journal'].value_counts())
    journals.reset_index(inplace=True)
    # rename count to number_of_articles
    journals.rename(columns={'count': 'number_of_articles'}, inplace=True)

    # get year from published-print
    df['year'] = df['published-print'].apply(lambda x: get_year(x))
    # change formatting to int
    df['year'] = df['year'].astype('Int64')
    # title column from list
    df['title'] = df['title'].apply(lambda x: x[0])
    # add https://doi.org/ to DOI column
    df['DOI'] = df['DOI'].apply(lambda x: 'https://doi.org/' + x)
    # strip the abstract column
    df['abstract'] = df['abstract'].apply(lambda x: x.strip())

    ####################################################################################################################
    # create a postgresql table for journals and insert values
    cur.execute("CREATE TABLE journals_new (journal VARCHAR(255), number_of_articles INT);")
    conn.commit()

    for i in range(len(journals)):
        number_of_articles = int(journals.iloc[i]['number_of_articles'])

        cur.execute("INSERT INTO journals_new (journal, number_of_articles) VALUES (%s, %s)",
                    (journals.iloc[i]['journal'], number_of_articles))
        conn.commit()
    ####################################################################################################################
    # create a new articles table in json lines format
    df = df[['title', 'abstract', 'journal', 'DOI', 'year', 'is-referenced-by-count']]
    df.to_json('temp/articles_new.jsonl', orient='records', lines=True)
