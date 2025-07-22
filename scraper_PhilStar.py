from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import os

results = []

# Step 1: Scrape headlines
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://www.philstar.com/")
    part_of_interest = page.inner_html('#inside_philstar_cells')
    soup = BeautifulSoup(part_of_interest, 'html.parser')

    rows = soup.select('tr')

    for row in rows:
        columns = row.find_all('td', class_='inside_cell')
        for col in columns:
            category = col.find('div', class_='inside_cell_section')
            title = col.find('h3')
            url = title.find('a', href=True) if title else None
            other_titles = col.find('ul')
            
            if category and title and url:
                results.append({
                    'Categories': category.get_text(strip=True),
                    'Titles': title.get_text(strip=True),
                    'Links': url['href']
                })
            
            if other_titles:
                for h3 in other_titles.find_all('h3'):
                    a_tag = h3.find('a', href=True)
                    if a_tag:
                        results.append({
                            'Categories': category.get_text(strip=True),
                            'Titles': a_tag.get_text(strip=True),
                            'Links': a_tag['href']
                        })

    browser.close()

# Step 2: Scrape article date and body
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.set_default_timeout(150000)

    for result in results:
        url = result['Links']
        result['Date'] = ''
        result['Article'] = ''
        try:
            page.goto(url)

            # Extract date
            if page.query_selector('.article__date-published'):
                date_raw = page.inner_text('.article__date-published').strip()
                try:
                    cleaned = date_raw.replace('|', '').strip()
                    dt = datetime.strptime(cleaned, "%B %d, %Y %I:%M%p")
                    result['Date'] = dt.date().isoformat()
                    result['Time'] = dt.time().strftime("%H:%M")
                except:
                    result['Date'] = date_raw  # fallback
                    result['Time'] = ''


            # Extract article body
            if page.query_selector('.article__writeup'):
                article_html = page.inner_html('.article__writeup')
                article_soup = BeautifulSoup(article_html, 'html.parser')
                paragraphs = article_soup.find_all('p')
                article_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
                result['Article'] = article_text

            # Extract article publisher only (skip author)
            if page.query_selector('.article__credits-author-pub'):
                byline_html = page.inner_html('.article__credits-author-pub')
                byline_soup = BeautifulSoup(byline_html, 'html.parser')

                # Get only the direct text (not from children like <span> or <a>)
                publisher_parts = [text.strip() for text in byline_soup.find_all(text=True, recursive=False) if text.strip()]

                publisher_raw = ' '.join(publisher_parts).strip()
                publisher_cleaned = re.sub(r'^[\s\-–—|]+', '', publisher_raw).strip()
                result['Publisher'] = publisher_cleaned if publisher_cleaned else 'Unknown'
            else:
                result['Publisher'] = 'Unknown'




        except Exception as e:
            print(f"Error on {url}: {e}")

    browser.close()


df = pd.DataFrame(results)
print(df)
df.to_csv('PhilStarScrape.csv', mode='a', header=not os.path.exists('PhilStarSample.csv'), index=False)
