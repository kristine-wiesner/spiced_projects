import psycopg2

# conn = psycopg2.connect(
#     database='postgres', user='kristine', password='abcdef',host='localhost', port='5432'
# )
# conn.autocommit = True
# cursor = conn.cursor()

# sql='''DROP DATABASE IF EXISTS final'''

# cursor.execute(sql)
# sql='''CREATE DATABASE final'''

# cursor.execute(sql)
# conn.close()

conn = psycopg2.connect(
    database='final', user='kristine', password='abcdef',host='localhost', port='5432'
)

cursor = conn.cursor()

deletion = ('''DROP TABLE reports;''','''DROP TABLE news;''','''DROP TABLE topics;''',
'''DROP TABLE esgai;''','''DROP TABLE company;''','''DROP TYPE controversy''')

for sql in deletion:
    cursor.execute(sql)

creation = ( 
'''CREATE TYPE controversy AS ENUM (
    'Very High Controversy','High Controversy','Moderate Controversy','Low Controversy','No Controversy');
''',
'''CREATE TABLE IF NOT EXISTS company (
    name VARCHAR(100) UNIQUE NOT NULL,
    ticker VARCHAR(5) UNIQUE NOT NULL PRIMARY KEY,
    sector VARCHAR(100),
    total_esg NUMERIC, 
    environmental_score NUMERIC,
    social_score NUMERIC, 
    governance_score NUMERIC, 
    controversy_score NUMERIC,
    controversy_assessment controversy
);''',
'''CREATE TABLE IF NOT EXISTS topics (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(250) UNIQUE NOT NULL
);''',
'''CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    company_id VARCHAR(5) NOT NULL,
    statement TEXT,
    lemma TEXT,
    topic_id INTEGER,
    probability NUMERIC,
    probabilities NUMERIC[],
    FOREIGN KEY (company_id)
    REFERENCES company(ticker)
    ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (topic_id)
    REFERENCES topics(id)
    ON UPDATE CASCADE ON DELETE SET NULL
);''',
'''CREATE TABLE IF NOT EXISTS news (
    id SERIAL PRIMARY KEY,
    company_id VARCHAR(5) NOT NULL,
    statement TEXT,
    lemma TEXT,
    topic_id INTEGER,
    probability NUMERIC,
    probabilities NUMERIC[],
    FOREIGN KEY (company_id)
    REFERENCES company(ticker)
    ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (topic_id)
    REFERENCES topics(id)
    ON UPDATE CASCADE ON DELETE SET NULL
);''',
'''CREATE TABLE IF NOT EXISTS gdelt (
    company_id INTEGER,
    id SERIAL PRIMARY KEY,
    gkg_record_id VARCHAR,
    date NUMERIC,
    source_collection_identifier NUMERIC,
    source_common_name VARCHAR,
    document_identifier TEXT,
    counts TEXT,
    counts_new TEXT,
    themes TEXT,
    enhanced_themes TEXT,
    locations TEXT,
    enhanced_locations TEXT,
    persons TEXT,
    enhanced_persons TEXT,
    organizations TEXT,
    enhanced_organizations TEXT,
    tone TEXT,
    enhanced_dates TEXT,
    gcam TEXT,
    sharing_image TEXT,
    related_images TEXT,
    social_image_embeds TEXT,
    social_video_embeds TEXT,
    quotations TEXT,
    all_names TEXT,
    amounts TEXT,
    translation_info TEXT,
    extras_xml TEXT
);''',
'''CREATE TABLE IF NOT EXISTS esgai (
    company_id VARCHAR(5),
    id SERIAL PRIMARY KEY,
    date VARCHAR(25),
    source VARCHAR(100),
    url TEXT,
    e BOOLEAN,
    s BOOLEAN,
    g BOOLEAN,
    organization VARCHAR(100),
    tone NUMERIC,
    positive_tone NUMERIC,
    negative_tone NUMERIC,
    polarity NUMERIC,
    activity_density NUMERIC,
    self_density NUMERIC,
    word_count NUMERIC,
    FOREIGN KEY (company_id)
    REFERENCES company(ticker)
    ON UPDATE CASCADE ON DELETE SET NULL
);''')

for sql in creation:
    cursor.execute(sql)

cursor.close()
conn.commit()
