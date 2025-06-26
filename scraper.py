from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
from transformers import pipeline
import os
import time
import re


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



articles_list = []
date_list = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.set_default_timeout(timeout=150000)

    for url in url_list:
        try:
            page.goto(url)
            part_of_interest = None

            # Scan for dates
            if page.query_selector('#art_plat'):
                date = page.inner_text('#art_plat')
            elif page.query_selector('#m-pd2'):
                date = page.inner_text('#m-pd2')
            else:
                date = " "

            if not date:
                print(f"Could not find date for {url}")
                date_list.append(" ")
                continue
            
            soup = BeautifulSoup(date, 'html.parser')
            date_text = soup.get_text(strip=True)

            if date_text:
                date_list.append(date_text)
            else:
                print(f"No date text found for {url}")
                date_list.append(" ")


            # Scan for specific content sections
            if page.query_selector('#FOR_target_content'):
                part_of_interest = page.inner_html('#FOR_target_content')
            elif page.query_selector('#TO_target_content'):
                part_of_interest = page.inner_html('#TO_target_content')
            elif page.query_selector('#elementor-widget-container'):
                part_of_interest = page.inner_html('#elementor-widget-container')

            if not part_of_interest:
                print(f"Could not find content for {url}")
                articles_list.append("Unable to retrieve article text")
                continue

            soup = BeautifulSoup(part_of_interest, 'html.parser')
            article_text = " ".join(p.get_text(strip=True) for p in soup.find_all('p'))

            if article_text:
                articles_list.append(article_text)
            else:
                print(f"No article text found for {url}")
                articles_list.append("Unable to retrieve article text")

        except Exception as e:
            print(f"Error processing {url}: {e}")
            articles_list.append("Unable to retrieve article text")
            continue

    browser.close()


df = pd.DataFrame(zip(date_list, category_list, titles_list, url_list, articles_list), columns=['Dates', 'Categories', 'Titles', 'Links', 'Articles'])
print(df)


col = df['Dates'].fillna('').astype(str)


pub_tail = col.str.split(r'\s*[\n/]\s*', n=1, expand=True)

df['Publisher'] = pub_tail[0].str.strip()                 
rest             = pub_tail[1].fillna('').str.strip()      

df['Publisher'] = df['Publisher'].str.split(' - ').str[-1].str.strip()

df['Time'] = rest.str.extract(r'(\d{1,2}:\d{2}\s*[AP]M)',  expand=False)
df['Dates'] = rest.str.extract(r'(\w+\s+\d{1,2},\s*\d{4})', expand=False)


df.to_csv('inquirer_articles.csv', mode='a', header=not os.path.exists('inquirer_articles.csv'), index=False)