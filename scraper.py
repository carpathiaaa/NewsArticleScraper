from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://www.inquirer.net/")
    part_of_interest = page.inner_html('#inqflxgl-wrap')
    soup = BeautifulSoup(part_of_interest, 'html.parser')

    categories = soup.find_all('div', class_='flx-m-cat')
    titles = soup.find_all('div', class_=['flx-m-head','flx-l-head'])
    
    category_list = []
    titles_list = []
    for category in categories:
        category_list.append(category.get_text(strip=True))

    for title in titles:
        titles_list.append(title.get_text(strip=True))


    url_list = []
    div_features = soup.find_all('div', class_=['flx-m-overlay','flx-l-overlay'])
    for div in div_features:
        a_tag = div.find('a', href=True)
        if a_tag:
            url_list.append(a_tag['href'])

    browser.close()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.set_default_timeout(timeout=150000)
    for url in url_list:
        page.goto(url)
        part_of_interest = page.inner_html('#article_content')
        soup = BeautifulSoup(part_of_interest, 'html.parser')
        articles = soup.find_all('p')
        for article in articles:
            print(article.get_text(strip=True))
    browser.close()


df = pd.DataFrame(zip(category_list, titles_list, url_list), columns=['Categories', 'Titles', 'Links'])
print(df)
