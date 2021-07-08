import psycopg2
import pandas as pd
import topicmodelling as tm
import numpy as np
from psycopg2.extensions import register_adapter, AsIs
from IPython.display import display

def get_dataframe_from_database(conn):
    select = '''
        SELECT name, n.statement, n.lemma FROM news n
        LEFT JOIN company c ON c.ticker = n.company_id;
    '''
    return pd.io.sql.read_sql_query(select,conn)

def update_database(conn,df):
    cursor = conn.cursor()
    create = '''CREATE TABLE IF NOT EXISTS news_alt (
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
    );'''
    insert = '''
        INSERT INTO news_alt (company_id, statement, lemma, topic_id, probability, probabilities)
        VALUES ((SELECT ticker FROM company WHERE LOWER(company.name) LIKE LOWER(%(name)s) LIMIT 1),
         %(statement)s, %(lemma)s, (SELECT id FROM topics WHERE topic = %(topic)s), %(probability)s, ARRAY[%(probabilities)s]);
    '''
    drop = '''DROP TABLE news;'''
    alter = '''ALTER TABLE news_alt RENAME TO news;'''

    cursor.execute(create)
    for record in df.to_dict('records'):
        cursor.mogrify(insert, record)
        cursor.execute(insert, record)
    cursor.execute(drop)
    cursor.execute(alter)
    conn.commit()
    cursor.close()
    return

if __name__ == "__main__":
    conn = psycopg2.connect(
        database='final', user='kristine', password='abcdef',host='localhost', port='5432'
    )
    #register_adapter(np.ndarray, tm.adapt_numpy_array)
    pd.set_option('display.max_columns', 1000)

    esg_df = get_dataframe_from_database(conn)
    stop_words = tm.get_stop_words(esg_df)

    lda, tf_feature_names, word_tf = tm.topic_modelling(esg_df, stop_words)
    topic_description_df = tm.top_words(lda, tf_feature_names,15)

    display(topic_description_df)

    esg_group_df = tm.attach_topic_distribution(esg_df, lda, word_tf)
    display(esg_group_df)

    x_df = esg_group_df[esg_group_df['name']=='Boeing Company']
    ks_df = tm.find_key_statement_for_topics(x_df, lda)
    display(ks_df)
    #update_database(conn, esg_group_df)
