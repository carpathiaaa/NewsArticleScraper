from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import os

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://www.philstar.com/")
    part_of_interest = page.inner_html('#inside_philstar_cells')
    soup = BeautifulSoup(part_of_interest, 'html.parser')

    rows = soup.select('tr')


    results = []

    for row in rows:
        columns = row.find_all('td', class_='inside_cell')
        for col in columns:
            category = col.find('div', class_='inside_cell_section')
            title = col.find('h3')
            url = title.find('a', href=True)
            other_titles = col.find('ul')
            
            if category and title:
                results.append(
                    {
                        'Categories' : category.get_text(strip=True),
                        'Titles' : title.get_text(strip=True),
                        'Links' : url['href']
                    }
                )
            if other_titles:
                for h3 in other_titles.find_all('h3'):
                    a_tag = h3.find('a')
                    a_tag_href = h3.find('a', href=True)
                    if a_tag:
                        results.append({
                            'Categories': category.get_text(strip=True),
                            'Titles': a_tag.get_text(strip=True),
                            'Links' : a_tag_href['href']
                        })
                        
                    

    links_list = [item['Links'] for item in results]
    #print(links_list)
    browser.close()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.set_default_timeout(timeout=150000)

    for url in links_list:
        print('Url', '\n')



#with sync_playwright() as p:



#df = pd.json_normalize(results)
#df.to_csv('PhilStarSample.csv', mode='a', header=not os.path.exists('PhilStarSample.csv'), index=False)