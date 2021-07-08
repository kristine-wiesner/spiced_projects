import psycopg2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display
from wordcloud import WordCloud, ImageColorGenerator
from sklearn.feature_extraction import text
from sklearn.decomposition import LatentDirichletAllocation as LDA
from sklearn.preprocessing import MinMaxScaler
from psycopg2.extensions import register_adapter, AsIs
from PIL import Image

topic_names = [
    'climate change strategy',
    'water efficiency',
    'energy efficiency',
    'carbon intensity',
    'environmental management system', 
    'equal opportunities', 
    'human rights', 
    'customer responsibility', 
    'health and safety',
    'support community',
    'business ethics',
    'compliance', 
    'shareholder democracy', 
    'socially responsible', 
    'executive compensation'
]

def get_dataframe_from_database(conn):
    select = '''
        SELECT name, r.statement, r.lemma FROM reports r
        LEFT JOIN company c ON c.ticker = r.company_id;
    '''
    return pd.io.sql.read_sql_query(select,conn)

def get_stop_words(df):
    """
    removing specific keywords, company names as well as
    english stop words not to be used in topic modelling
    """
    sp_stop_words = [
        'plc', 'group', 'target',
        'track', 'capital', 'holding',
        'annualreport', 'esg', 'bank', 
        'report','long', 'make',
        'table','content', 'wells', 'fargo', 'nxp', 
        'letter', 'ceo', 'about', 'united', 'states', 'scope'
    ]
    for name in df.name.unique():
        for word in name.split():
            sp_stop_words.append(word.lower())
    return text.ENGLISH_STOP_WORDS.union(sp_stop_words)

def corpus_wide_term_frequencies(df, stop_words,image_file):
    """
    create a word cloud for the whole corpus displaying the most frequent terms 
    using a given back ground image
    """
    large_string = ' '.join(df.lemma)
    
    mask = np.array(Image.open(image_file))
    font = 'arial.ttf'
    colors = ImageColorGenerator(mask)
    
    word_cloud = WordCloud(font_path = font,
        background_color="#effbf9",
        mask = mask, 
        max_words=5000, 
        width=900, 
        height=700,
        stopwords=stop_words,
        color_func=colors,
        contour_width=1, 
        contour_color='white'
    )
    
    plt.figure(figsize=(20,20))
    word_cloud.generate(large_string)
    plt.imshow(word_cloud, interpolation='bilinear')
    plt.axis("off")
    return plt

def bigram_analysis(df, stop_words):
    """
    using Tf-Idf vectorization to find the most frequent bigrams in the corpus
    """
    bigram_tf_idf_vectorizer = text.TfidfVectorizer(stop_words=stop_words, ngram_range=(2,2), min_df=10, use_idf=True)
    bigram_tf_idf = bigram_tf_idf_vectorizer.fit_transform(df.lemma)
    words = bigram_tf_idf_vectorizer.get_feature_names()
    total_counts = np.zeros(len(words))
    for t in bigram_tf_idf:
        total_counts += t.toarray()[0]

    count_dict = (zip(words, total_counts))
    count_dict = sorted(count_dict, key=lambda x:x[1], reverse=True)[0:10]
    words = [w[0] for w in count_dict]
    counts = [w[1] for w in count_dict]
    x_pos = np.arange(len(words)) 

    plt.figure(figsize=(15, 5))
    plt.subplot(title='10 most common bi-grams')
    sns.barplot(x_pos, counts, color = '#E9C46A') #palette='crest'
    plt.xticks(x_pos, words, rotation=45) 
    plt.xlabel('bi-grams')
    plt.ylabel('tfidf')
    ax = plt.gca()
    ax.set_facecolor('None')
    plt.rcParams['figure.facecolor'] = 'None'
    return plt

def top_words(model, feature_names, n_top_words):
    rows = []
    for topic_idx, topic in enumerate(model.components_):
        message = ", ".join([feature_names[i] for i in topic.argsort()[:-n_top_words - 1:-1]])
        rows.append(["Topic #%d: " % (topic_idx + 1), message])
    return pd.DataFrame(rows, columns=['topic', 'keywords'])

def topic_modelling(df, stop_words, n_components=5): #ichanged here
    """
    extract topics from the corpus using Latent Dirichlet Allocation model
    """
    word_tf_vectorizer = text.CountVectorizer(stop_words=stop_words, ngram_range=(1,1))
    word_tf = word_tf_vectorizer.fit_transform(df.lemma)
    lda = LDA(random_state=42, n_components=n_components,learning_decay=0.3)
    lda.fit(word_tf)
    tf_feature_names = word_tf_vectorizer.get_feature_names()

    return lda,tf_feature_names,word_tf

def word_cloud(model, tf_feature_names, index):
    imp_words_topic=""
    comp = model.components_[index]
    vocab_comp = zip(tf_feature_names, comp)
    sorted_words = sorted(vocab_comp, key = lambda x:x[1], reverse=True)[:50]
    for word in sorted_words:
        imp_words_topic = imp_words_topic + " " + word[0]
    return WordCloud(
        background_color="white",
        width=600, 
        height=600, 
        contour_width=3, 
        contour_color='steelblue'
    ).generate(imp_words_topic)
    
def display_topics(lda, tf_feature_names):
    topics = len(lda.components_)
    fig = plt.figure(figsize=(20, 20 * topics / 5))

    for i, topic in enumerate(lda.components_):
        ax = fig.add_subplot(topics, 3, i + 1)
        ax.set_title(topic_names[i], fontsize=20)
        wordcloud = word_cloud(lda, tf_feature_names, i)
        ax.imshow(wordcloud)
        ax.set_facecolor('None')
        ax.axis('off')
    return plt

def attach_topic_distribution(df, lda,word_tf):
    transformed = lda.transform(word_tf)
    a = [np.argmax(distribution) for distribution in transformed]
    b = [np.max(distribution) for distribution in transformed]
    df2 = pd.DataFrame(zip(a,b,transformed), columns=['topic', 'probability', 'probabilities'])
    return pd.concat([df, df2], axis=1)
    
def clear_database(conn):
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM topics;''')
    conn.commit()
    cursor.close()
    return

def insert_topic_names(conn, topics):
    cursor = conn.cursor()
    for topic in topics:
        cursor.execute('''INSERT INTO topics(topic) VALUES (%s);''', (topic,))
    conn.commit()
    cursor.close()
    return

def update_database(conn,df):
    cursor = conn.cursor()
    create = '''CREATE TABLE IF NOT EXISTS reports_alt (
        id SERIAL PRIMARY KEY,
        company_id VARCHAR(5) NOT NULL,
        statement TEXT,
        lemma TEXT,
        topic INTEGER,
        probability NUMERIC,
        probabilities NUMERIC[],
        FOREIGN KEY (company_id)
        REFERENCES company(ticker)
        ON UPDATE CASCADE ON DELETE CASCADE
    );'''
    insert = '''
        INSERT INTO reports_alt (company_id, statement, lemma, topic, probability, probabilities)
        VALUES ((SELECT ticker FROM company WHERE LOWER(company.name) LIKE LOWER(%(name)s) LIMIT 1),
         %(statement)s, %(lemma)s,  %(topic)s, %(probability)s, ARRAY[%(probabilities)s]);
    '''
    drop = '''DROP TABLE reports;'''
    alter = '''ALTER TABLE reports_alt RENAME TO reports;'''

    cursor.execute(create)
    for record in df.to_dict('records'):
        cursor.mogrify(insert, record)
        cursor.execute(insert, record)
    cursor.execute(drop)
    cursor.execute(alter)
    conn.commit()
    cursor.close()
    return

def adapt_numpy_array(numpy_array):
    list = numpy_array.tolist()
    return AsIs(list)

def compare_core_initiatives(df):
    esg_focus = pd.crosstab(df.name, df.topic)
    scaler = MinMaxScaler(feature_range = (0, 1))
    esg_focus_norm = pd.DataFrame(scaler.fit_transform(esg_focus), columns=esg_focus.columns)
    esg_focus_norm.index = esg_focus.index
    sns.set(rc={'figure.figsize':(15,10)})
    sns.heatmap(esg_focus_norm, annot=False, linewidths=.5, cmap='Blues')
    return plt

def retrieve_key_statements_for_topic(df, topic, topic_idx):
    """
    extracts the statements which are releveant to a given topic
    """
    topic_discussions = df[df['topic'] == topic_idx]
    topic_discussions = topic_discussions[topic_discussions['probability'] > 0.89]
    topic_discussions = topic_discussions.sort_values('probability', ascending=False)
    rows = [] 
    for i, row in topic_discussions.iterrows():
        rows.append([row['topic'], row.probability, row.statement])

    return pd.DataFrame(rows, columns=['topic', 'probability', 'statement'])

def find_key_statement_for_topics(df, model):
    row_list=[]
    for topic_idx, topic in enumerate(model.components_):
        topic_df = retrieve_key_statements_for_topic(df, topic, topic_idx)
        if (topic_df.size > 0):
            topic_df.iloc[0].topic = topic_df.iloc[0].topic + 1 
            row_list.append(topic_df.iloc[0])
    return pd.DataFrame(row_list)

def show_topic_probability_distribution(df):
    """
    displays the distribution of statements which are specific to one distinct topic
    this probability is used for retrieving the key statements in each topic
    """
    df.probability.hist(bins=50, figsize=(10,8), color='steelblue')
    plt.axvline(0.89, color='coral', linestyle='--')
    plt.title('Primary topic distribution')
    plt.xlabel('probability')
    plt.ylabel('density')
    return plt

def plot_top_words(model, feature_names, n_top_words, title):
    """
    displays the top words from the five most important topics
    found by the used model (here it's LDA)
    """
    fig, axes = plt.subplots(1, 5, figsize=(30, 15), sharex=True)
    axes = axes.flatten()
    for topic_idx, topic in enumerate(model.components_):
        top_features_ind = topic.argsort()[:-n_top_words - 1:-1]
        top_features = [feature_names[i] for i in top_features_ind]
        weights = topic[top_features_ind]

        ax = axes[topic_idx]
        ax.barh(top_features, weights, height=0.7, color = '#E76F51')
        ax.set_title(f'Topic {topic_idx +1}',
                     fontdict={'fontsize': 30})
        ax.invert_yaxis()
        ax.tick_params(axis='both', which='major', labelsize=20)
        ax.set_facecolor('None')

        for i in 'top right left'.split():
            ax.spines[i].set_visible(False)
        fig.suptitle(title, fontsize=40)

    plt.subplots_adjust(top=0.90, bottom=0.05, wspace=0.90, hspace=0.3)
    return plt


if __name__ == "__main__":
    conn = psycopg2.connect(
        database='final', user='kristine', password='abcdef',host='localhost', port='5432'
    )
    register_adapter(np.ndarray, adapt_numpy_array)
    #clear_database(conn)
    esg_df = get_dataframe_from_database(conn)
    stop_words = get_stop_words(esg_df)
    # TODO corpus_wide_term_frequencies(esg_df, stop_words)
    # TODO bigram_analysis(esg_df, stop_words)
    lda, tf_feature_names, word_tf = topic_modelling(esg_df, stop_words)
    topic_description_df = top_words(lda, tf_feature_names,15)

    pd.set_option( 'display.max_columns', 1000)
    #display(topic_description_df)

    # TODO think of more fitting topic names (see csv)
    topic_description_df.to_csv("topic_description.csv")
    #insert_topic_names(conn, topic_names)
    # TODO display_topics(lda, tf_feature_names)

    esg_group_df = attach_topic_distribution(esg_df, lda, word_tf)
    ks_df = find_key_statement_for_topics(esg_group_df, lda)
    display(esg_group_df)
    display(ks_df)
    update_database(conn, esg_group_df)
    # compare_core_initiatives(esg_group_df).show()
    #show_topic_probability_distribution(esg_group_df).show()
    topic = topic_names # TODO maybe don't do this here, alternatively create key statement table
    key_statement_df = retrieve_key_statements_for_topic(esg_group_df, topic)
    #display(key_statement_df)