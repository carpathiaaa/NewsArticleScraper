from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
from transformers import pipeline
import os
import time

summarizer = pipeline("summarization", model="facebook/bart-large-cnn", framework="pt")


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


summaries = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.set_default_timeout(timeout=150000)
    for url in url_list:
        page.goto(url)
        part_of_interest = None

        if page_query := page.query_selector('#FOR_target_content'):
            part_of_interest = page.inner_html('#FOR_target_content')
        elif page_query := page.query_selector('#TO_target_content'):
            part_of_interest = page.inner_html('#TO_target_content')

        soup = BeautifulSoup(part_of_interest, 'html.parser')
        article_text = " ".join(p.get_text(strip=True) for p in soup.find_all('p'))

        summary = summarizer(
                article_text,
                max_length=130,
                min_length=30,
                do_sample=False
            )[0]['summary_text']

        summaries.append(summary)
        print(f"✅ Summarized: {url}")



        #articles_list = []
        #for article in articles:
        #    articles_list.append(article.get_text(strip=True))
    browser.close()

#print(summary[0]['summary_text'])

df = pd.DataFrame(zip(category_list, titles_list, url_list, summaries), columns=['Categories', 'Titles', 'Links', 'Summaries'])
print(df)

