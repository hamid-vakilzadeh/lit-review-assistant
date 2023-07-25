from habanero import Crossref, cn
from typing import List, Union
import jsonlines
import streamlit as st


@st.cache_data(show_spinner='updating reference in APA format...')
def get_citation(
        doi,
        format: str = "text",
        style: str = "apa"
) -> Union[List[str] | str]:
    """
    Get citation for a given doi
    :param doi: get citation for a given doi or list of dois
    :type doi: Union[List[str], str]
    :param format: requested format of the citation, eg. text, bibtex, ris, etc.
    :type format: str
    :param style: citation style, eg. apa, chicago-fullnote-bibliography, etc.
    :type style: str
    :return: citation in the requested format as a string or list of strings
    :rtype: Union[List[str], str]
    """
    cr = Crossref(mailto=st.secrets["crossref_mailto"])
    return cn.content_negotiation(ids=doi, format=format, style=style)


def get_journal_from_article(
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
        article_details = cr.works(article)
        issns += article_details['message']['ISSN']

    # get articles for all journals
    journal_details = cr.journals(ids=issns, works=True, limit=limit, cursor='*', progress_bar=True)

    # get all articles
    new_items = []
    for i in journal_details:
        new_items += [z['message']['items'] for z in i]
    new_items = [item for sublist in new_items for item in sublist]

    # remove duplicated articles
    non_duplicated_items = []
    for i in new_items:
        if i not in non_duplicated_items:
            non_duplicated_items.append(i)

    return non_duplicated_items


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

    # get journal ISSNs
    non_duplicated_items = get_journal_from_article(articles)

    # write articles to jsonl file
    with jsonlines.open('temp/articles.jsonl', mode='a') as writer:
        for i in non_duplicated_items:
            writer.write(i)

    # get available styles
    styles = cn.csl_styles()

    # get citation for a given doi

