
import pandas as pd
import psycopg2
import esgpdfanalyzer as analyzer
import requests
from bs4 import BeautifulSoup
from IPython.display import display

organizations = [
    # ["boeing","boeing company"],
    # ["netflix", "netflix inc."],
    # ["abbott laboratories","abbott laboratories"],
    # ["amazon com", "amazon.com inc."],
    # ["analog devices", "analog devices inc."],
    # ["coca cola", "coca cola company"],
    # ["exxon mobil", "exxon mobil corp."],
    # ["facebook", "facebook inc."],
    ["wells fargo", "wells fargo"]
    # ["general motors", "general motors"],
    # ["citigroup", "citigroup inc."]
]
pd.set_option('display.max_columns', 1000)

def clear_database(conn):
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM news;''')
    conn.commit()
    cursor.close()
    return

def get_urls_for_organization(conn, organization):
    select = f'''
        SELECT url from esgai WHERE organization = '{organization[0]}';
    '''
    #SELECT url from esgai WHERE organization = '{organization[0]}' AND url LIKE '%{organization[0]}%';
        
    cursor = conn.cursor()
    cursor.execute(select)
    urls = cursor.fetchall()
    return urls

def get_text_from_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
        "Accept-Encoding": "*",
        "Connection": "keep-alive"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        html_page = res.content
        res.close()
        return soup_html(html_page), 0
    except requests.exceptions.Timeout:
        print (f"Timeout occurred: %s",url)
    except requests.exceptions.ConnectionError:
        print (f"Connection Error: %s",url)
    except requests.exceptions.ChunkedEncodingError:
        print (f"ChunkedEncoding Error: %s",url)
    return "", 1

def soup_html(html_page):
    soup = BeautifulSoup(html_page, 'html.parser')
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.find_all(text=True)

    output = ''
    blacklist = [
        '[document]',
        'noscript',
        'header',
        'html',
        'meta',
        'head', 
        'input',
        'script',
        'style', 
        'font', 
        'family', 
        'div', 'px','san','serif','width','height','padding',
        'privacy policy', 'amazon buy','index', 'file',
        'endif', 'if', 'gt', 'javascript', 'ie',
        'request unsuccesful'
        # there may be more such as "style", etc.
    ]

    for t in text:
        if t.parent.name.lower() not in blacklist:
            output += '{} '.format(t)

    return output

def extract_web_content():
    entries = []
    for organization in organizations:
        urls = get_urls_for_organization(conn, organization)
        texts = []
        errors = 0
        display(urls)
        for url in urls[100:201]:
            text, err = get_text_from_url(url[0])
            texts.append(text)
            errors = errors + err
        text = ''.join(texts)
        print(f'errors: {errors}')
        entries.append({'company' : organization[1], 'contents' : text})
    return pd.DataFrame.from_dict(entries)

def update_database(conn,df):
    cursor = conn.cursor()

    insert = '''
        INSERT INTO news (company_id, statement, lemma)
        VALUES ((SELECT ticker FROM company WHERE LOWER(company.name) LIKE LOWER(%(company)s) LIMIT 1), 
        %(statement)s, %(lemma)s);
    '''

    for record in df.to_dict('records'):
        cursor.mogrify(insert, record)
        cursor.execute(insert, record)
    conn.commit()
    cursor.close()
    return

if __name__ == "__main__":
    conn = psycopg2.connect(
        database='final', user='kristine', password='abcdef',host='localhost', port='5432'
    )
    #clear_database(conn)

    # 1. extract web content
    esg_articles_df = extract_web_content()
    display(esg_articles_df)
    # 2. extract statements from records
    esg_statements_df = analyzer.extract_from_articles(esg_articles_df)
    display(esg_statements_df)
    # 3. tokenize statements
    esg_lemma_df = analyzer.create_lemma(esg_statements_df)
    display(esg_lemma_df)
    update_database(conn,esg_lemma_df)
