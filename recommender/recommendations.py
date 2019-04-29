from recommender.models import Movie, Similarity

#Load similar movies from database based on similarity score
def load_identical_movies(movie, n):
    similarities = Similarity.objects.filter(
        first_movie=movie.movie_id,
        second_movie__liked=None
    ).exclude(
        second_movie__movie_id=movie.movie_id
    ).order_by('-similarity_score')

    similar_movies = []

    for similarity in similarities[:n]:
        similar_movie = similarity.second_movie
        similar_movies.append((similar_movie.title, similar_movie.movie_id))
    return similar_movies


def get_similar_movies(movies):
    all_similar_movies = []
    for movie in movies:
        all_similar_movies.extend(load_identical_movies(movie, 20))
    movie_ids = [movie_id for movie_title, movie_id in all_similar_movies]
    return Movie.objects.filter(movie_id__in=movie_ids)

#Filter similar movies from the already liked movies
def exclude_liked_movies(similar_unliked_movies, similar_liked_movies):
    similar_liked_ids = similar_liked_movies.values_list('movie_id', flat=True)
    unliked = similar_unliked_movies.exclude(movie_id__in=similar_liked_ids)[:20]
    liked = similar_liked_movies[:20]
    return liked, unliked

#Load recommendations based on liked and unliked movies
def load_recommendations():
    rated_movies = Movie.objects.filter(liked__isnull=False)

    liked_movies = rated_movies.filter(liked=True, comparable=True)
    similar_liked_movies = get_similar_movies(liked_movies)
    similar_liked_movies.order_by('?')

    unliked_movies = rated_movies.filter(liked=False, comparable=True)
    similar_unliked_movies = get_similar_movies(unliked_movies)
    similar_unliked_movies.order_by('-rating_mean')

    liked, unliked = exclude_liked_movies(similar_unliked_movies, similar_liked_movies)
    return liked, unliked
