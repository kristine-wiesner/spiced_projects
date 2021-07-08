import pandas as pd
import numpy as np
from sklearn.decomposition import NMF

movies = [
'Jurassic Park (1993)',
'Mrs. Doubtfire (1993)',
'Silence of the Lambs, The (1991)',
'101 Dalmatians (1996)',
'Gladiator (2000)', 
'Ghostbusters (a.k.a. Ghost Busters) (1984)',
'Fargo (1996)',
'Minority Report (2002)',
'2 Fast 2 Furious (Fast and the Furious 2, The) (2003)',
'Alice in Wonderland (2010)'
]


def get_recommendations(films):
    movies_df  = pd.read_csv('../project/data/movies.csv')
    ratings_df = pd.read_csv('../project/data/ratings.csv')
    merged_df = ratings_df.merge(movies_df, on = 'movieId', how = 'left')
    user_df = merged_df.pivot_table(index='userId',columns='title',values='rating')
    user_df.fillna(user_df.mean(), inplace=True)
    rated_movies = list(user_df.columns)
    empty_list = [np.nan]*len(rated_movies)
    ratings_dict = dict(zip(rated_movies, empty_list))

    for movie, rating in films.items():
        ratings_dict[movie] = rating

    new_user_df = pd.DataFrame(list(ratings_dict.values()), index=rated_movies, dtype=float)
    new_user_df = new_user_df.T

    nmf = NMF(n_components=5,max_iter=200, init='random', random_state=10)
    nmf.fit(user_df)

    Q = nmf.components_

    new_user_df_filled = new_user_df.fillna(user_df.mean())
    P = nmf.transform(new_user_df_filled)
    predictions = np.dot(P,Q)

    recommendations = pd.DataFrame(predictions, columns=user_df.columns)
    not_rated_mask = np.isnan(new_user_df.values[0])
    not_rated = recommendations.columns[not_rated_mask]
    items_to_recommend = recommendations[not_rated]
    items_to_recommend = items_to_recommend.T
    items_to_recommend.columns = ['predicted_rating']

    return items_to_recommend.sort_values(by='predicted_rating', ascending=False)[:10].index.tolist()
