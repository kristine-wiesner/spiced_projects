import pandas as pd
import PyPDF2
import sys
import spacy
import re
import string
import gensim
import psycopg2


sys.stdout.reconfigure(encoding='utf-8')
#spacy.cli.download("en_core_web_sm")

pdf_path = "./data/SustainabilityReports/"

esg_pdf_rows = [
    ["abbott laboratories","abbott_2019.pdf"],
    ["amazon.com inc.", "amazon_2020.pdf"],
    ["analog devices inc.", "analog_2019.pdf"],
    ["boeing company","boeing_2020.pdf"],
    ["coca cola company", "coca_2019.pdf"],
    ["exxon mobil corp.", "exxon_mobil.pdf"],
    ["facebook inc.", "fb_2019.pdf"],
    ["netflix inc.", "netflix_2020.pdf"],
    ["wells fargo", "wells_2020.pdf"],
    ["general motors", "GM_2019.pdf"],
    ["citigroup inc.", "citi_2019.pdf"]
]


def extract_content(filename):
    """
    Extracts text from a PDF
    """
    pdf_stream = open(filename, "rb")
    pdf = PyPDF2.PdfFileReader(pdf_stream)
    text = [pdf.getPage(i).extractText() for i in range (0, pdf.getNumPages())]
    return "\n".join(text)

def load_articles():
    """
    Puts PDF content into data frame
    """
    esg_pdf_df = pd.DataFrame(esg_pdf_rows, columns=['company','file'])
    contents =[extract_content(f"{pdf_path}{file}") for file in esg_pdf_df['file']]
    esg_pdf_df['contents'] = contents
    esg_pdf_df.drop('file', axis =1,inplace=True)
    return esg_pdf_df


def extract_from_articles(df):
    rows = df.values.tolist()
    esg_statements_df = pd.DataFrame(extract_statements(rows), columns=['company','statement'])
    return esg_statements_df

def extract_statements(rows):
    """
    extract statenents from the raw text using a spacy model
    """
    nlp = spacy.load("en_core_web_sm", disable=['ner'])
    nlp.max_length = 2000000
    dict_list = []
    for row in rows:
        statement_rows=extract_sentences(nlp,row[1])
        for sentence in statement_rows:
            company_dict= {}
            company_dict["company"] = row[0]
            company_dict["statement"] = sentence
            dict_list.append(company_dict)
    return dict_list

def remove_non_ascii(text):
  printable = set(string.printable)
  return ''.join(filter(lambda x: x in printable, text))

def not_header(line):
  return not line.isupper()

def extract_sentences(nlp, text):
    """
    clean sentences from unwanted characters, spaces,
    line breaks, heade numbers and urls
    """
    sentences = []
    lines = []
    
    text = remove_non_ascii(text)
    prev = ""
    for line in text.split('\n'):
        if (line.startswith(' ') or not prev.endswith('.')):
            prev = prev + ' ' + line
        else:
            lines.append(prev)
            prev = line
        
    lines.append(prev)

    for line in lines:
        line = re.sub(r'^\s?\d+(.*)$', r'\1', line)
        line = line.strip()
        line = re.sub('\s?-\s?', '-', line)
        line = re.sub(r'\s?([,:;\.])', r'\1', line)
        line = re.sub(r'\d{5,}', r' ', line)
        line = re.sub(r'((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*', r' ', line)
        line = re.sub('\s+', ' ', line)
        for part in list(nlp(line).sents):
            sentences.append(str(part).strip())
   
    return sentences

def tokenize(sentence):
    gen = gensim.utils.simple_preprocess(sentence, deacc=True)
    return ' '.join(gen)

def lemmatize(nlp, text):
    doc = nlp(text) 
    lemma = []
    for token in doc:
        if (token.lemma_ not in ['-PRON-']):
            lemma.append(token.lemma_)
          
    return tokenize(' '.join(lemma))
  
def create_lemma(df):
    """
    creating lemmas from sentences using spacy
    words are converted in their basic form
    """
    nlp = spacy.load("en_core_web_sm", disable=['ner'])
    rows = df.values.tolist()
    lemmas = []
    for row in rows:
        lemmas.append(lemmatize(nlp, row[1]))
    df['lemma'] = lemmas
    return df

def update_database(conn,df):
    cursor = conn.cursor()

    insert = '''
        INSERT INTO reports (company_id, statement, lemma)
        VALUES ((SELECT ticker FROM company WHERE LOWER(company.name) LIKE LOWER(%(company)s) LIMIT 1), 
        %(statement)s, %(lemma)s);
    '''

    for record in df.to_dict('records'):
        cursor.mogrify(insert, record)
        cursor.execute(insert, record)
    conn.commit()
    cursor.close()
    return

def clear_database(conn):
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM reports;''')
    conn.commit()
    cursor.close()
    return

if __name__ == "__main__":
    conn = psycopg2.connect(
        database='final', user='kristine', password='abcdef',host='localhost', port='5432'
    )
    clear_database(conn)
    # 1. extract pdf content
    esg_articles = load_articles()
    print(esg_articles)
    # 2. extract statements from records
    esg_statements = extract_from_articles(esg_articles)
    print(esg_statements)
    # 3. tokenize statements
    esg_lemma = create_lemma(esg_statements)
    print(esg_lemma)

    update_database(conn,esg_lemma)
