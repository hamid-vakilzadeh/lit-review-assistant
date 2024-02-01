import pandas as pd
from habanero import Crossref, cn
from typing import List, Union
import jsonlines
import streamlit as st
from bs4 import BeautifulSoup
from tqdm import tqdm
import requests
from undetected_chromedriver import Chrome, ChromeOptions


@st.cache_data(show_spinner=False)
def get_citation(
        doi: Union[List[str], str],
        format: str = "text",
        style: str = "apa"
) -> Union[List[str] | str]:
    """
    Get citation for a given doi
    :param doi: get citation for a given doi or list of dois
    :param format: requested format of the citation, eg. text, bibtex, ris, etc.
    :param style: citation style, eg. apa, chicago-fullnote-bibliography, etc.
    :return: citation in the requested format as a string or list of strings
    """
    cr = Crossref(mailto=st.secrets["crossref_mailto"])
    return cn.content_negotiation(ids=doi, format=format, style=style)


def get_apa_citation(article: dict):
    st.session_state.citations[article['id']] = get_citation(article['doi'])


def get_journal_issn(
        article_doi: list,
        limit: int = 20
) -> list:
    """
    get all articles for one or more journals from one or more dois from that journal
    :param article_doi: a list of dois from one or more journals
    :param limit: number of articles to return (max=1000)
    :return: a list of articles' metadata
    """

    issns = []
    for article in article_doi:
        try:
            article_details = cr.works(article)
            issns += article_details['message']['ISSN']
        except Exception:
            print(f'Could not get {article}')
    return issns


def get_journal_details(issn: list, limit: int = 20):
    # get articles for all journals
    return cr.journals(ids=issn, works=True, limit=limit, cursor='*', progress_bar=True)


def get_article_with_doi(doi: str) -> dict:
    cr = Crossref(mailto=st.secrets["crossref_mailto"])

    try:
        docs = cr.works(doi)
        soup = BeautifulSoup(docs['message']['abstract'], features="lxml").text
        authors_dict = docs['message']['author']
        family_names = []
        for item in range(len(authors_dict)):
            family_names.append(authors_dict[item]['family'])
        article_info = {
            'text': soup.strip(),
            'year': str(docs['message']['published']['date-parts'][0][0]).strip(),
            'cite_counts': '',
            'title': docs['message']['title'][0].strip(),
            'journal': docs['message']['container-title'][0].strip(),
            'doi': docs['message']['URL'].strip(),
            'id': doi.replace('https://doi.org/', '').replace('/', '-').strip(),
            'authors': ', '.join(family_names),
            # 'relevance': round((1 - round(docs['distances'][0][i], 2)) * 100),
            'type': 'abstract'
        }
        return article_info
    except Exception:
        raise Exception(f'Could not get {doi}: Please ensure the doi is correct. if the error persists try uploading the PDF.')


if __name__ == '__main__':
    cr = Crossref(mailto=st.secrets["crossref_mailto"])

    # pass example doi to get metadata
    articles = [
        'https://doi.org/10.1016/j.jacceco.2022.101536',  # Journal of Accounting and Economics
        'https://doi.org/10.1111/1475-679X.12486',  # Journal of Accounting Research
        'https://doi.org/10.1016/j.aos.2022.101425',  # Accounting, Organizations and Society
        'https://doi.org/10.1111/1911-3846.12880',  # Contemporary Accounting Research
        'https://doi.org/10.1007/s11142-023-09774-9',  # Review of Accounting Studies
        'https://doi.org/10.1016/j.jaccpubpol.2022.107016',  # Journal of Accounting and Public Policy
        'https://doi.org/10.1177/0148558X231175952',  # Journal of Accounting Auditing and Finance
        'https://doi.org/10.1016/j.acclit.2019.03.001',  # Journal of Accounting Literature
        'https://doi.org/10.1111/j.1468-5957.2012.02295.x'  # Journal of Business Finance and Accounting
    ]

    articles = [
        'https://doi.org/10.1111/abac.12310',  # Abacus
        'https://doi.org/10.5465/amj.2020.1579',  # Academy of Management Journal
        'https://doi.org/10.5465/amr.2023.0202',  # Academy of Management Review
        'https://doi.org/10.1080/00014788.2023.2241135',  # Accounting and Business Research
        'https://doi.org/10.2308/HORIZONS-2022-191',  # Accounting Horizons
        'https://doi.org/10.1016/j.aos.2023.101535',  # Accounting Organizations and Society
        'https://doi.org/10.1177/0001839219893691',  # Administrative Science Quarterly
        'https://doi.org/10.1016/j.adiac.2023.100710',  # Advances in Accounting
        'https://doi.org/10.1108/S1058-749720230000030001',  # Advances in Taxation
        'https://doi.org/10.1257/aer.20171397 ',  # American Economic Review
        'https://doi.org/10.2308/AJPT-2020-107',  # Auditing: A Journal of Practice and Theory
        'https://doi.org/10.2308/BRIA-2022-017',  # Behavioral Research in Accounting
        'https://doi.org/10.1111/1911-3846.12925',  # Contemporary Accounting Research
        'https://doi.org/10.3982/ECTA17482',  # Econometrica
        'https://doi.org/10.1287/isre.2021.0528',  # Information Systems Research
        'https://doi.org/10.2308/ISSUES-2021-125',  # Issues in Accounting Education
        'https://doi.org/10.1016/j.jacceco.2023.101638',  # Journal of Accounting and Economics
        'https://doi.org/10.1016/j.jaccpubpol.2023.107132',  # Journal of Accounting and Public Policy
        'https://doi.org/10.1177/0148558X231210899',  # Journal of Accounting Auditing and Finance
        'https://doi.org/10.1016/j.jaccedu.2022.100796',  # Journal of Accounting Education
        'https://doi.org/10.1108/JAL-03-2023-0042',  # Journal of Accounting Literature
        'https://doi.org/10.1111/1475-679X.12518',  # Journal of Accounting Research
        'https://doi.org/10.1111/jbfa.12781',  # Journal of Business Finance and Accounting
        'https://doi.org/10.1093/jcr/ucad016',  # Journal of Consumer Research
        'https://doi.org/10.1111/jofi.13307',  # Journal of Finance
        'https://doi.org/10.1017/S0022109023000431',  # Journal of Financial and Quantitative Analysis
        'https://doi.org/10.1016/j.jfineco.2023.103777',  # Journal of Financial Economics
        'https://doi.org/10.2308/ISYS-2021-040',  # Journal of Information Systems
        'https://doi.org/10.2308/JMAR-2023-022',  # Journal of Management Accounting Research
        'https://doi.org/10.1177/00222429231207636',  # Journal of Marketing
        'https://doi.org/10.1177/00222437231196824',  # Journal of Marketing Research
        'https://doi.org/10.1086/726232',  # Journal of Political Economy
        'https://doi.org/10.2308/JATA-2021-013',  # Journal of the American Taxation Association
        'https://doi.org/10.1287/mnsc.2020.02453',  # Management Science
        'https://doi.org/10.25300/MISQ/2022/16764',  # MIS Quarterly
        'https://doi.org/10.17310/ntj.2018.4.01',  # National Tax Journal
        'https://doi.org/10.1093/qje/qjad025',  # Quarterly Journal of Economics
        'https://doi.org/10.2308/JOGNA-19-012',  # Journal of Governmental and Nonprofit Accounting
        'https://doi.org/10.1007/s11142-023-09810-8 ',  # Review of Accounting Studies
        'https://doi.org/10.1007/s11156-021-01007-x ',  # Review of Quantitative Finance and Accounting
        'https://doi.org/10.1002/smj.3556',  # Strategic Management Journal
        'https://doi.org/10.2308/TAR-2020-0554',  # The Accounting Review
    ]

    articles = [
        'https://doi.org/10.48550/arXiv.2211.07349',
        "https://api.crossref.org/works/10.48550/arXiv.2211.07349/agency",
        "https://api.crossref.org/works/10.2308/TAR-2020-0554/agency",
    ]

    # get journal ISSNs
    issn_list = get_journal_issn(articles)

    journal_details = []
    for i in issn_list[51:]:
        journal_details.append(get_journal_details(i))

    # '1058-7497' failed
    # '1547-7185' failed
    # article_details = cr.journals(query='MIS Quarterly')

    # get all articles
    new_items = []
    for i in journal_details:
        new_items += [z['message']['items'] for z in i]
    new_items = [item for sublist in new_items for item in sublist]
    pd.to_pickle(new_items, 'database/articles.pkl')

    # remove duplicated articles
    non_duplicated_items = []
    for i in tqdm(new_items):
        if i not in non_duplicated_items:
            non_duplicated_items.append(i)

    non_duplicated_items_pd = pd.DataFrame(non_duplicated_items)
    non_duplicated_items_pd.isna().sum()

    # drop duplicates on DOI
    non_duplicated_items_pd.drop_duplicates(subset=['DOI'], inplace=True, ignore_index=True)

    # add a page column
    non_duplicated_items_pd['web_page'] = ''

    # replace nan in abstract column with ''
    non_duplicated_items_pd['abstract'].fillna('', inplace=True)
    # count the abstracts that are empty

    # get unique publishers
    publishers = non_duplicated_items_pd['publisher'].unique().tolist()
    # create a dictionary of publishers and their articles
    publishers_dict = []
    for i in publishers:
        publishers_dict.append({i:0})

    # get a webdriver
    browser = Chrome()

    # size of non_duplicated_items_pd
    all_article_count = len(non_duplicated_items_pd)
    i = 0
    this_publisher_index = 0

    while i < all_article_count:
        # current publisher
        current_publisher_name, current_publisher_count = list(publishers_dict[this_publisher_index].items())[0]
        this_publisher = non_duplicated_items_pd[non_duplicated_items_pd['publisher'] == current_publisher_name]
        this_publisher.reset_index(inplace=True, drop=True)

        if current_publisher_count < len(this_publisher):
            # get the row that is equal to current_publisher_count
            this_row = this_publisher.iloc[current_publisher_count]

            # if the abstract of this row is not empty
            if this_row['abstract'] == '':
                # get the html of the page
                this_page = browser.get(this_row['URL'])
                html = browser.page_source
                # add it to the Web_page column at the intersection of this_row['URL']
                non_duplicated_items_pd.loc[non_duplicated_items_pd['URL'] == this_row['URL'], 'web_page'] = html

                # update the publisher count
                publishers_dict[this_publisher_index][current_publisher_name] += 1
                # update the index
                i += 1
            else:
                publishers_dict[this_publisher_index][current_publisher_name] += 1
                i += 1
            # print progress
            print(f'{i}/{all_article_count} articles scraped, {current_publisher_name} {publishers_dict[this_publisher_index][current_publisher_name]} articles scraped')

        # update the publisher index
        if this_publisher_index == 14:
            this_publisher_index = 0
        else:
            this_publisher_index += 1



    # get available styles
    styles = cn.csl_styles()

    get_citation(doi="https://doi.org/10.2308/TAR-2021-0645")
    cr = Crossref(mailto=st.secrets["crossref_mailto"])
    response = cr.works("10.2308/TAR-2021-0645")
    article = get_article_with_doi("10.2308/TAR-2021-0645")
