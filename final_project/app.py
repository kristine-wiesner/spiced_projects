import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import os
import psycopg2
import plotly.graph_objects as go
import topicmodelling as tm
import gensimanalysis as ga
from plotly.subplots import make_subplots

#Connect to PostgreSQL#

conn = psycopg2.connect( database='final', user='kristine', password='abcdef',host='localhost', port='5432')


@st.cache (hash_funcs={psycopg2.extensions.connection: id}, show_spinner=False, suppress_st_warning=True,
          allow_output_mutation=True)
def load_full_data():
    select = '''
        SELECT c.name, c.total_esg, c.environmental_score, c.social_score, c.governance_score, 
              c.controversy_score, c.controversy_assessment, e.url, e.tone, e.positive_tone,
              e.negative_tone, e.polarity, e.E, e.S, e.G, e.date, e.source, e.word_count
        FROM esgai e
        LEFT JOIN company c ON c.ticker = e.company_id;
    '''
    return pd.io.sql.read_sql_query(select,conn)

@st.cache (hash_funcs={psycopg2.extensions.connection: id}, show_spinner=False, suppress_st_warning=True,
          allow_output_mutation=True)
def load_topic_data():
    select = '''
        SELECT c.name, r.statement, r.lemma, r.topic, r.probability, r.probabilities FROM reports r
        LEFT JOIN company c ON c.ticker = r.company_id;
    '''
    return pd.io.sql.read_sql_query(select,conn)


@st.cache (hash_funcs={psycopg2.extensions.connection: id}, show_spinner=False, suppress_st_warning=True,
          allow_output_mutation=True)
def load_news_topic_data():
    select = '''
        SELECT c.name, n.statement, n.lemma, t.topic, n.probability, n.probabilities FROM news n
        LEFT JOIN company c ON c.ticker = n.company_id
        LEFT JOIN topics t ON t.id = n.topic_id;
    '''
    return pd.io.sql.read_sql_query(select,conn)


def main():
    ###Format Settings### 
    icon_path = os.path.join(".", "Logo", "klimpact_logo3.png")
    page_icon_path = os.path.join(".", "Logo", "symbol3.png")
    st.set_page_config(page_title="klimpact", page_icon=page_icon_path,
                       layout='wide', initial_sidebar_state="collapsed")
    _,logo, _ = st.beta_columns(3)
    logo.image(icon_path, use_column_width=True)
    style = ("text-align:center; padding: 0px;"
             "font-size: 150%")
    title = f"<h1 style='{style}'>An ESG Analysis of S&P 500 Companies </h1><br><br>"
    st.write(title, unsafe_allow_html=True)

    ###Database###
    full_df = load_full_data()
    topic_df = load_topic_data()
    news_topic_df = load_news_topic_data()

    ###Sidebar Display Features###
    st.sidebar.title("Display Features")
    check_communicated = st.sidebar.checkbox("Sustainability Reports Analysis")
    check_perceived = st.sidebar.checkbox("News Articles Analysis")

    ###Main Display Page# 
    with st.spinner(text="Fetching Data..."):
        companies = full_df['name'].sort_values().unique().tolist()

    ###Company Selection##
    company = st.selectbox("Choose a Company", companies)
    if company and company != "Choose a Company":
        ###Show ESG Risk Scores###
        st.plotly_chart(show_esg_values(full_df, company), use_container_width=True)
        
         ###Show Controversy Scores Default Display###
        st.plotly_chart(show_controversy_level(full_df.loc[full_df['name'] == company]['controversy_score'].iat[0]))
        company_topic_df = topic_df[topic_df['name'] == company]
       
        ###Shows Sustainability Analysis#
        if company_topic_df.size > 0 and check_communicated:
            st.header(f"Sustainability Report Analysis of {company}")
            
            ###Word Cloud##
            show_topic_modelling(company_topic_df,"esg9.png")


        ###News Article Analysis###

        ###List of News Sources According to Tones###
        company_news_topic_df = news_topic_df[news_topic_df['name'] == company]
        st.write('---')
        if company_news_topic_df.size > 0 and check_perceived:
            st.header(f"News Articles Analysis of {company}")
            st.subheader("News Articles Sentiment Analysis")
            st.markdown("This data is taken from ESG AI Research, where they used GDELT (Global Database for Events, Language and Tones), which is Google's repository of global News, Event, Forums etc... For this project only sources from News Medias are considered.")
            org_df = full_df[full_df['name'] == company]
            org_df = org_df.rename(columns={"url": "URL", "tone" : "Tone", "positive_tone": "Positive Tone", "source": "Source", "word_count": "WordCount",
                                "negative_tone": "Negative Tone", "polarity" : "Polarity", "e" : "E", "s": "S", "g" : "G"})

            
            st.write(f"Number of News Sources: {len(org_df)}")
            st.dataframe(show_tones_from_news_sources(org_df))

            st.markdown("")
            st.markdown("")
            st.markdown("These are some random list of the articles, categorized according to E, S and G relevance.")
            col_radio, col_table= st.beta_columns((1, 3))
            category = col_radio.radio('News Categories', ['E','S','G'])
            col_table.markdown(show_random_esg_news(org_df, category))


            st.markdown("")
            st.markdown("")
            st.markdown("This line graph visualizes the Average Tone over time.")
            col_metric, col_graph= st.beta_columns((1, 3))
            line_metric = col_metric.radio("Choose Tone", ["Tone", "Negative Tone", "Positive Tone"])
            col_graph.altair_chart(show_trends_over_time(org_df, line_metric, company), use_container_width=True)



            st.markdown("")
            st.markdown("")
            st.markdown("This Scatterplot visualizes the Tone of all the articles over time. The larger the circle, the more words it contained")
            st.altair_chart(show_article_tone(org_df), use_container_width=True)

            topic_modelling_news(company_news_topic_df)
    return


###FUNCTION DEFINITIONS###

###ESG Risk Scores###
def show_esg_values(df, company):
    st.subheader('ESG Risk Scores')
    #st.markdown("These are based on Yahoo Finance's Sustainability Scores which are referenced from Sustainalytics. Total Score in dark green (max = 60), adds up E in orange, S in yellow and G in coral respectively with max values of 20 each factor.")


    fig = make_subplots(rows=1, cols=4, specs=[[{'type':'domain'}, {'type':'domain'}, {'type':'domain'}, {'type':'domain'}]])     

    max_val = df['total_esg'].max()
    esg_val = df.loc[df['name'] == company]['total_esg'].iat[0]
    values =[esg_val, 60-esg_val]
    labels = [" ", ""]
    colors = ['264653', '65baa4',]

    max_val_e = df['environmental_score'].max()
    e_val = df.loc[df['name'] == company]['environmental_score'].iat[0]
    values_e =[e_val, 20-e_val]
    labels_e = [" ", ""]
    colors_e = ['f4a261','65baa4']

    max_val_s = df['social_score'].max()
    s_val = df.loc[df['name'] == company]['social_score'].iat[0]
    values_s =[s_val, 20-s_val]
    labels_s = [" ", ""]
    colors_s = ['e9c46a','65baa4']

    max_val_g = df['governance_score'].max()
    g_val = df.loc[df['name'] == company]['governance_score'].iat[0]
    values_g =[g_val, 20-g_val]
    labels_g = [" ", ""]
    colors_g = ['e76f51','65baa4']

    pie1 = go.Pie(labels=labels,values=values,hole=0.5,showlegend=False,textinfo='none',
                sort=False,rotation=270,marker = dict(colors= colors), name="ESG total")
    pie2 = go.Pie(labels=labels_e,values=values_e,hole=0.5,showlegend=False,textinfo='none',
                sort=False,rotation=270,marker = dict(colors= colors_e), name="Environment")
    pie3 = go.Pie(labels=labels_s,values=values_s,hole=0.5,showlegend=False,textinfo='none',
                sort=False,rotation=270,marker = dict(colors= colors_s), name="Social")
    pie4 = go.Pie(labels=labels_g,values=values_g,hole=0.5,showlegend=False,textinfo='none',
                sort=False,rotation=270,marker = dict(colors= colors_g), name="Governance")
    fig.add_trace(pie1,1,1)
    fig.add_trace(pie2,1,2)
    fig.add_trace(pie3,1,3)
    fig.add_trace(pie4,1,4)

    fig.update_layout(
        
        annotations=[dict(text='Total', x=0.075, y=0.5, font_size=13, showarrow=False),
                        dict(text='Environment', x=0.37, y=0.5, font_size=13, showarrow=False),
                        dict(text='Social', x=0.63, y=0.5, font_size=13, showarrow=False),                 
                        dict(text='Governance', x=0.95, y=0.5, font_size=13, showarrow=False)]
    )
    return fig



###Controversy Level###
def show_controversy_level(score):
    st.subheader('Controversy Level')
    #st.markdown("Sustainalytic's Controversy Ratings (used by Yahoo finance) are multi-dimensional risk rating of a company's exposure to industy-specific risks and how well these company manage them.")
    #st.markdown("Neglegible = 0, Low = 1, Moderate = 2, High = 3, Very High = 4,  Severe = 5")
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        domain = {'x': [0, 1], 'y': [0, 1]},
        #title = {'text': "Controversy Level", 'font': {'size': 24}},
        gauge = {
            'axis': {'range': [None, 5], 'tickcolor': "white", 'tickmode': "array" },
            'bar': {'color': "#faf1dc"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                    {'range': [0, 1], 'color': "#264653"},
                    {'range': [1, 2], 'color': "#2a9d8f"},
                    {'range': [2, 3], 'color': "#e9c46a"},
                    {'range': [3, 4], 'color': "#f4a261"},
                    {'range': [4, 5], 'color': "#e76f51"}],
            'threshold': {
                'line': {'color': "#e76f51", 'width': 0.1},
                'thickness': 0.75,
                'value': 490}}))

    fig.update_layout(paper_bgcolor = "#effbf9", font = {'color': "#264653", 'family': "arial"})
    fig.update_traces(value=score)
    fig.update_traces(gauge ={'axis' : {'ticktext':['None','Low','Moderate','High','Very High','Severe'],'tickvals':[0,1,2,3,4,5]}})
    return fig


###Topic Modeling for Sustainability Reports###
def show_topic_modelling(df, image_file):
    st.subheader("Word Cloud")
    st.markdown("Heres a visual representation of the most frequent words used in the Sustainability Report. The size of the word is relative to its importance.")
    stop_words = tm.get_stop_words(df)
    plt = tm.corpus_wide_term_frequencies(df, stop_words, image_file)
    st.pyplot(plt)
    plt.figure()

    st.subheader("Bi-gram")
    st.markdown("Using  Term Frequency - Inverse Document Frequency (TF-IDF) these are the most common sequence of two words or bigrams found in the Report")
    plt = tm.bigram_analysis(df, stop_words)
    st.pyplot(plt)
    plt.figure()

    st.subheader("LDA Model")
    st.markdown("SKLearn's Latent Dirichlet Allocation (LDA) Topic Modeling is used here to learn topics from ESG Reports and here are the top 5 topics.")
    lda, tf_feature_names, word_tf = tm.topic_modelling(df, stop_words, 5)
    topic_description_df = tm.top_words(lda, tf_feature_names, 15)

    plt = tm.plot_top_words(lda, tf_feature_names, 15, "")
    st.pyplot(plt)
    plt.figure()
    
    st.subheader("Key statements for each topic")
    st.markdown("These are the key sentences that has the highest probability which are relevant to the top 5 topics")
    ks_df = tm.find_key_statement_for_topics(df, lda)
    #st.dataframe(ks_df)

    fig = go.Figure(data=[go.Table(
        header=dict(values=list(['Topic','Statement','Probability']),
                    fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=[ks_df.topic, ks_df.statement,ks_df.probability],
                fill_color='lavender',
                align='left'))
    ])
    st.plotly_chart(fig, use_container_width=True)
    return



###News Article Sentiment Analysis###
def show_tones_from_news_sources(df):
    display_cols = ["Source","Tone", "Positive Tone","Negative Tone","Polarity"] 
    return df[display_cols]

def show_random_esg_news(df, category):
    url_df = df[df[category] == True]
    link_df = url_df[["date", "URL"]].sample(5).copy()
    link_df["ARTICLE"] = link_df.URL.apply(get_clickable_name)
    return link_df[["date", "ARTICLE"]].to_markdown(index=False)

def show_trends_over_time(df, line_metric, company):
    df['date'] = pd.to_datetime(df['date'], infer_datetime_format=True)
    plot_df = df.groupby(by=[pd.Grouper(key='date', freq='D')])[line_metric].mean().reset_index()
    plot_df["ESG"] = company.title()
    metric_chart = alt.Chart(plot_df, title="Trends Over Time").mark_line().encode(
    x=alt.X("yearmonthdate(date):O", title="date"),
    y=alt.Y(f"{line_metric}:Q"),
    color=alt.Color("ESG", legend=None),
    strokeDash=alt.StrokeDash("ESG", sort=None,
        legend=alt.Legend(
            title=None, symbolType="stroke", symbolFillColor="gray",
            symbolStrokeWidth=4, orient="top",
            ),
        ),
    tooltip=["date", alt.Tooltip(line_metric, format=".3f")]
    )
    return metric_chart.properties(height=340,width=200).interactive()

def show_article_tone(df):
    scatter = alt.Chart(df, title="Article Tone").mark_circle().encode(
        x="Negative Tone:Q",
        y="Positive Tone:Q",
        size="WordCount:Q",
        color=alt.Color("Polarity:Q", scale=alt.Scale(scheme='darkblue')),
        tooltip=[alt.Tooltip("Polarity", format=".3f",),
                    alt.Tooltip("Negative Tone", format=".3f"),
                    alt.Tooltip("Positive Tone", format=".3f"),
                    alt.Tooltip("date"),
                    alt.Tooltip("WordCount", format=",d"),
                    alt.Tooltip("Source", title="Site")]
        ).properties(
            height=450
        ).interactive()
    return scatter

def get_clickable_name(url):
    try:
        T = metadata_parser.MetadataParser(url=url, search_head_only=True)
        title = T.metadata["og"]["title"].replace("|", " - ")
        return f"[{title}]({url})"
    except:
        return f"[{url}]({url})"


###News Article Sentiment Topic Modeling###

def topic_modelling_news(df):
    stop_words = tm.get_stop_words(df)
    lda, tf_feature_names, word_tf = tm.topic_modelling(df, stop_words, 5)
    topic_description_df = tm.top_words(lda, tf_feature_names,15)

    st.subheader("Word Cloud")
    st.markdown("Heres a visual representation of the most frequent words found in the News Artcle.")

    plt = tm.corpus_wide_term_frequencies(df, stop_words, "esg9c.png")
    st.pyplot(plt)
    plt.figure()

    st.subheader("Bigram")
    st.markdown("These are the most common bigrams found in the New Articles")
    plt = tm.bigram_analysis(df, stop_words)
    st.pyplot(plt)
    plt.figure()

    st.subheader("LDA Model")
    st.markdown("These are the Top 5 topics extracted from the News Articles")
    plt = tm.plot_top_words(lda, tf_feature_names, 15, " ")
    st.pyplot(plt)
    plt.figure()

    st.subheader("Key statements for each topic")
    st.markdown("These are the Key staments extracted from the News Articles")
    esg_df = df.drop(columns=['topic','probability','probabilities'])
    esg_group_df = tm.attach_topic_distribution(esg_df, lda, word_tf)
    ks_df = tm.find_key_statement_for_topics(esg_group_df, lda)
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(['Topic','Statement','Probability']),
                    fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=[ks_df.topic, ks_df.statement,ks_df.probability],
                fill_color='lavender',
                align='left'))
    ])
    st.plotly_chart(fig, use_container_width=True)

    return




if __name__ == "__main__":
    main()
    