from time import sleep
import psycopg2
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import selenium.webdriver as webdriver
from selenium.webdriver.common.by import By
from tools.doi import CrossRefClient


def get_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


conn = psycopg2.connect(database="hamid", user="postgres")

cur = conn.cursor()  # cursor to execute SQL commands


def getHTMLText(url):
    payload = ""
    headers = {
        "cookie": "AAA_SessionId=z131i3z5yoexv0ezjbd02d45; American_Accounting_AssociationMachineID=638191874475082726; American_Accounting_Association=UserName%3Daaa71600%26UserPwd%3D65A8F345189B6ED34CCFE06B07F8D52931DA7139",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9,fa;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Cookie": "hum_aaa_visitor=d4c25ac0-aed9-47ab-aea9-5cfc4c255e0d; rl_page_init_referrer=RudderEncrypt%3AU2FsdGVkX1%2FQQ%2FVOxD9breiO4MsEl26DnnZ%2B0rg5gc6XfZdcPwIlRYKyjxuZK2IO; rl_page_init_referring_domain=RudderEncrypt%3AU2FsdGVkX1%2BQpQaURLRvXKJeMcynEqBgiPlPx%2F8PSmZbYDnnkK2VUGouiLYOpqVa; rl_user_id=RudderEncrypt%3AU2FsdGVkX19nzrezj1g6a2zHAdEJNN5ZHwaojQ8fyg0%3D; rl_trait=RudderEncrypt%3AU2FsdGVkX1%2BzT3JYqnA7XEnOjJugEOqlm4EWS%2BZn9Ok%3D; rl_group_id=RudderEncrypt%3AU2FsdGVkX19tZAjMrF%2Ful79vmqLLwx7BfNRNu%2Byf9r0%3D; rl_group_trait=RudderEncrypt%3AU2FsdGVkX19HzPIyaUDVqIitlpk9Li8ISt%2ButGL3rA4%3D; rl_anonymous_id=RudderEncrypt%3AU2FsdGVkX19maYXLlYXlTx5BR35FCtPGqki0cgoJGge%2FlPBDvwJSlZPCVRG4bvqL1FOJE7xsC52FjwbAjVPf%2Bg%3D%3D; rl_session=RudderEncrypt%3AU2FsdGVkX19VUlnVXOLI2ljtV%2FAn3qV8qicWgnckhGn3TAbIm0hDmBbIWRpufLuGEvgNiVRdcuE2EUq9splBz4y1Hxv1ZJNPilElFwp27mx386X0uGuWbYbKGUAFyiq76d3EvcBJVCWGe%2Fop6%2FVwvA%3D%3D; American_Accounting_AssociationMachineID=638068071237851677; GDPR_57_publications.aaahq.org=true; American_Accounting_Association=UserName=aaa71600&UserPwd=65A8F345189B6ED34CCFE06B07F8D52931DA7139; AAA_SessionId=tg2sl5qs3phlq3nnwcfvgbf3; KEY=1230907*1502093:2685873516:3901119989:1",
        "DNT": "1",
        "Referer": "https://publications.aaahq.org/jata/issue/21/1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Not.A / Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"'
    }

    response = requests.request("GET", url, data=payload, headers=headers)
    if response.status_code == 200:
        return response
    else:
        raise Exception(f"Error: {response.status_code}")


if __name__ == '__main__':

    urls = []
    # for each journal and issue
    for i in tqdm(range(21, 28)):
        # sleep(1)
        for j in (1, 2, 3, 4):
            try:
                # 'Accounting, Organizations and Society\n'
                # 'Contemporary Accounting Research\n'
                # 'Journal of Accounting And Economics\n'
                # 'Journal of Accounting Research\n'
                # 'Journal of the American Taxation Association\n'
                # 'Review of Accounting Studies\n'

                url = f"https://publications.aaahq.org/jata/issue/{i}/{j}"
                html = getHTMLText(url)
                soup = BeautifulSoup(html.content, "html.parser")

                # find all articles
                articles = soup.find_all("h5", class_="item-title")

                # get url of each article
                for article in articles:
                    urls.append(article.find("a").get("href"))
            except Exception as e:
                print(e)

    # add each url to the database
    for url in tqdm(urls):
        journal, article_type, volume, issue, page, aaa_id, title = url.split("/")[1:]
        cur.execute(f"INSERT INTO articles "
                    f"(aaa_id, url, journal, volume, issue, page, title) "
                    f"VALUES ('{aaa_id}', '{url}', '{journal}', '{volume}', '{issue}', '{page}', '{title}');")
        conn.commit()

    driver = get_browser()
    # get the abstract and doi of each article
    cur.execute("SELECT url from articles where citation is null ;")
    urls = cur.fetchall()
    for url in urls:
        current_article = url[0].replace('/article/', '/article-abstract/')
        driver.get(f'https://publications.aaahq.org/{current_article}')
        html = driver.find_element(by=By.TAG_NAME, value='body').get_attribute('innerHTML')
        soup = BeautifulSoup(html, "html.parser")
        article_doi = soup.find("div", class_="citation-doi").text.strip()
        try:
            article_abstract = soup.find("section", class_="abstract").text
        except AttributeError:
            article_abstract = None

        # pdf_only
        pdf_only_article = False
        if "This content is only available via PDF." in soup.text:
            pdf_only_article = True

        cur.execute(f"UPDATE articles "
                    f"SET doi = '{article_doi}', pdf_only='{pdf_only_article}', abstract = $$'{article_abstract}'$$ "
                    f"WHERE url = '{url[0]}';")
        conn.commit()

        print(f"Updated {url}")

    # get the doi information
    cur.execute("SELECT url, doi from articles where citation is null;")
    urls = cur.fetchall()
    for url in urls:
        cite = CrossRefClient().doi2apa(doi=f'{url[1]}')
        cited = cite.encode('latin-1').decode('utf-8').replace(url[1], '').strip()
        cur.execute(f"UPDATE articles "
                    f"SET citation = '{cited}' "
                    f"WHERE url = '{url[0]}';")
        conn.commit()
        print(f"Updated {url}")

    cur.execute("SELECT title, abstract, doi from articles")
    cur.fetchall()

    cur.execute("SELECT count(distinct aaa_id) from articles where abstract is not null;")
    cur.fetchone()

    conn.close()
