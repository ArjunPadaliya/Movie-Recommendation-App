import argparse
import os
import pandas as pd
import numpy as np
import zipfile
import requests
import sqlite3
import logging
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#Dataset links online
dataset_link = "http://files.grouplens.org/datasets/movielens/ml-20m.zip"
youtube_trailors_link = "http://files.grouplens.org/datasets/movielens/ml-20m-youtube.zip"
DEFAULT_PATH_TO_DB = os.path.join(BASE_DIR, 'db.sqlite3')


#Download data from internet and extract data
def download_data(download_path):
    print("Downloading Dataset")
    dataset_path = os.path.join(download_path, 'ml-20m.zip')
    response = requests.get(dataset_link, stream=True)
    with open(dataset_path, 'wb') as handle:
        for data in tqdm(response.iter_content()):
            handle.write(data)

    print("Downloading youtube trailors")
    trailors_path = os.path.join(download_path, 'ml-20m-youtube.zip')
    response = requests.get(youtube_trailors_link, stream=True)
    with open(trailors_path, 'wb') as handle:
        for data in tqdm(response.iter_content()):
            handle.write(data)

    print("Extracting dataset")
    zip_ref = zipfile.ZipFile(dataset_path, 'r')
    zip_ref.extractall(download_path)
    zip_ref.close()

    print("Extracting youtube trailors")
    zip_ref = zipfile.ZipFile(trailors_path, 'r')
    zip_ref.extractall(download_path + os.sep + 'ml-20m')
    zip_ref.close()

#Load dataset into pandas dataframe
def load_dataset(input_dataset_path):
    if input_dataset_path is not None:
        print("Loading Dataset")
        movies = pd.read_csv(os.path.join(input_dataset_path, 'movies.csv'))
        movie_ratings = pd.read_csv(os.path.join(input_dataset_path, 'ratings.csv'), usecols=['movieId', 'rating'])
        genome_scores = pd.read_csv(os.path.join(input_dataset_path, 'genome-scores.csv'))
        genome_tags = pd.read_csv(os.path.join(input_dataset_path, 'genome-tags.csv'))
        imdb_links = pd.read_csv(os.path.join(input_dataset_path, 'links.csv'))
        youtube_links = pd.read_csv(os.path.join(input_dataset_path, 'ml-youtube.csv'))
        links = pd.merge(imdb_links, youtube_links, on='movieId', how='left')[['movieId', 'imdbId', 'youtubeId']]
        movie_tags_as_text = pd.merge(genome_scores, genome_tags, on='tagId')[['movieId', 'tag', 'relevance']]
        return genome_scores, genome_tags, movies, movie_ratings, links, movie_tags_as_text
    else:
        download_path = str(os.getcwd())
        download_data(download_path)
        dataset = load_dataset(download_path + os.sep + 'ml-20m')
    return dataset

#Connecting to database
def connect_database(database_path):
    if database_path is None:
        database_path = DEFAULT_PATH_TO_DB
    db = sqlite3.connect(database_path)
    return db

#Join movie tags as one single string
def concatenate_tags(tags):
    tags_as_str = ' '.join(set(tags))
    return tags_as_str


def calculate_ratings(movie_ratings):
    avg_ratings = movie_ratings.groupby('movieId')['rating'].agg({
        'rating_mean': 'mean',
        'rating_median': 'median',
        'num_ratings': 'size'
    })
    return avg_ratings.reset_index()

#Calculate movie similarity
def calculate_similarity(genome_scores, genome_tags, movies, movie_ratings):
    tf_idf = TfidfVectorizer()

    relevant_tags = genome_scores[genome_scores.relevance > 0.3][['movieId', 'tagId']]
    movie_tags = pd.merge(relevant_tags, genome_tags, on='tagId', how='left')[['movieId', 'tagId']]
    movie_tags['tagId'] = movie_tags.tagId.astype(str)
    tags_per_movie = movie_tags.groupby('movieId')['tagId'].agg({'movie_tags': concatenate_tags}).reset_index()

    avg_movie_ratings = calculate_ratings(movie_ratings)

    movies_with_ratings = pd.merge(movies, avg_movie_ratings, on='movieId')
    dataset = pd.merge(movies_with_ratings, tags_per_movie, on='movieId', how='left')

    dataset.rename(columns={'movieId': 'movie_id'}, inplace=True)

    movies_with_tags = dataset.movie_tags.notnull()
    movies_without_ratings = dataset.movie_tags.isnull()
    dataset_with_tags = dataset[movies_with_tags].reset_index(drop=True)
    uncomparable_movies = dataset[(~movies_with_tags) | (movies_without_ratings)]

    print("calculating movie to movie similarity...")

    vectorized = tf_idf.fit_transform(dataset_with_tags.movie_tags)
    m2m_matrix = pd.DataFrame(cosine_similarity(vectorized))
    index = dataset_with_tags['movie_id']
    m2m_matrix.columns = [str(index[int(col)]) for col in m2m_matrix.columns]
    m2m_matrix.index = [index[idx] for idx in m2m_matrix.index]
    m2m_similarity = m2m_matrix.stack().reset_index()
    m2m_similarity.columns = ['first_movie_id', 'second_movie_id', 'similarity_score']
    return m2m_similarity, dataset_with_tags, uncomparable_movies

#Write data into the database tables
def write_database(df, table_name, db_connection):
    total_length = len(df)
    step = int(total_length / 100)

    with tqdm(total=total_length) as pbar:
        for i in range(0, total_length, step):
            subset = df[i: i + step]
            subset.to_sql(table_name, db_connection, if_exists='append', index=False)
            pbar.update(step)

#Initiate database tables with column names and initiate filling of database tables
def fill_database(db_connection, movie_to_movie_similarity, dataset_with_tags, uncomparable_movies, links, movie_tags_as_text):

    links_col_order = ['movie_id', 'imdb_id', 'youtube_id']
    links.rename(columns={'movieId': 'movie_id', 'imdbId': 'imdb_id', 'youtubeId': 'youtube_id'}, inplace=True)

    tags_col_order = ['movie_id', 'tag', 'relevance']
    movie_tags_as_text.rename(columns={'movieId': 'movie_id'}, inplace=True)

    dataset_col_order = ['movie_id', 'title', 'genres', 'num_ratings', 'rating_median', 'rating_mean', 'comparable']
    dataset_with_tags['comparable'] = True
    uncomparable_movies['comparable'] = False

    print("writing movies with tags to DB...")
    write_database(dataset_with_tags[dataset_col_order], 'recommender_movie', db_connection)

    print("writing movies without tags to DB...")
    write_database(uncomparable_movies[dataset_col_order], 'recommender_movie', db_connection)

    print("writing online links to DB...")
    write_database(links[links_col_order], 'recommender_onlinelink', db_connection)

    print("writing movie tags to DB...")
    write_database(movie_tags_as_text[tags_col_order], 'recommender_tag', db_connection)

    print("writing movie similarities to DB...")
    write_database(movie_to_movie_similarity, 'recommender_similarity', db_connection)


def main(dataset_path, database_path):
    genome_scores, genome_tags, movies, movie_ratings, links, movie_tags_as_text = load_dataset(dataset_path)
    db_connection = connect_database(database_path)
    movie_to_movie_similarity, dataset_with_tags, uncomparable_movies = calculate_similarity(genome_scores, genome_tags, movies, movie_ratings)
    fill_database(db_connection, movie_to_movie_similarity, dataset_with_tags, uncomparable_movies, links, movie_tags_as_text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download MovieLens dataset & fill Django database")
    parser.add_argument('-i', '--input-dataset', type=str, help="Path to dataset folder if already downloaded")
    args = parser.parse_args()
    main(args.input_dataset, args.database)
