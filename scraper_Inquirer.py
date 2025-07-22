from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import os

results = []

# Step 1: Scrape headlines, categories, links
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://www.inquirer.net/")
    
    part_of_interest = page.inner_html('#inqflxgl-wrap')
    soup = BeautifulSoup(part_of_interest, 'html.parser')

    categories = soup.find_all('div', class_='flx-m-cat')
    titles = soup.find_all('div', class_=['flx-m-head', 'flx-l-head'])
    url_blocks = soup.find_all('div', class_=['flx-m-overlay', 'flx-l-overlay'])

    for i in range(min(len(categories), len(titles), len(url_blocks))):
        category = categories[i].get_text(strip=True)
        title = titles[i].get_text(strip=True)
        a_tag = url_blocks[i].find('a', href=True)

        if a_tag:
            results.append({
                'Categories': category,
                'Titles': title,
                'Links': a_tag['href'],
                'Date': '',
                'Time': '',
                'Publisher': '',
                'Article': ''
            })

    browser.close()

# Step 2: Visit each article to extract date, time, publisher, and article text
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.set_default_timeout(timeout=150000)

    for result in results:
        url = result['Links']
        try:
            page.goto(url)

            # ----------------------------
            # PUBLISHER extraction from <a> inside #art_plat
            # ----------------------------
            result['Publisher'] = 'Unknown'
            if page.query_selector('#art_plat'):
                art_plat_html = page.inner_html('#art_plat').strip()
                soup_art_plat = BeautifulSoup(art_plat_html, 'html.parser')
                publisher_tag = soup_art_plat.find('a')
                if publisher_tag:
                    result['Publisher'] = publisher_tag.get_text(strip=True)

            # ----------------------------
            # DATE and TIME extraction (from #art_plat or #m-pd2)
            # ----------------------------
            date_raw = ''
            for selector in ['#art_plat', '#m-pd2']:
                if page.query_selector(selector):
                    date_raw = page.inner_text(selector).strip()
                    break

            result['Date'] = ''
            result['Time'] = ''
            if date_raw:
                soup = BeautifulSoup(date_raw, 'html.parser')
                date_text = soup.get_text(strip=True)

                # Extract time and date using regex
                time_match = pd.Series([date_text]).str.extract(r'(\d{1,2}:\d{2}\s*[AP]M)', expand=False)[0]
                date_match = pd.Series([date_text]).str.extract(r'(\w+\s+\d{1,2},\s*\d{4})', expand=False)[0]

                result['Time'] = time_match if pd.notna(time_match) else ''
                result['Date'] = date_match if pd.notna(date_match) else ''

            # ----------------------------
            # ARTICLE CONTENT extraction
            # ----------------------------
            article_html = ''
            for selector in ['#FOR_target_content', '#TO_target_content', '#elementor-widget-container']:
                if page.query_selector(selector):
                    article_html = page.inner_html(selector)
                    break

            if article_html:
                soup = BeautifulSoup(article_html, 'html.parser')
                paragraphs = soup.find_all('p')
                article_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
                result['Article'] = article_text if article_text else 'Unable to retrieve article text'
            else:
                result['Article'] = 'Unable to retrieve article text'

        except Exception as e:
            print(f"Error processing {url}: {e}")
            result['Article'] = 'Unable to retrieve article text'
            result['Publisher'] = 'Unknown'
            result['Date'] = ''
            result['Time'] = ''

    browser.close()

# Step 3: Export to CSV
df = pd.DataFrame(results)
df.to_csv('InquirerScrape.csv', mode='a', header=not os.path.exists('InquirerScrape.csv'), index=False)
print(df)
