import operator
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from recommender.models import Movie, OnlineLink
from recommender.recommendations import load_recommendations
from functools import reduce
from django.db.models import Q

#Search movies with their titles from database
def search_movies(request):
    query = request.get('search_query')
    movies = Movie.objects.all()
    query_elements = query.split()
    filtered = movies.filter(reduce(operator.and_,(Q(title__icontains=q) for q in query_elements)))
    return {'search_results': filtered}


def home(request):
    if request.method == 'GET' and len(request.GET) > 0:
        search_results = search_movies(request.GET)
        return render(request, 'home.html', context=search_results)

    uncomparable = Movie.objects.filter(comparable=False).order_by('?')[:20]
    context = {
        'uncomparable': uncomparable,
        'home' : 'active'
    }
    return render(request, 'home.html', context = context)


def detail(request, movie_id):
    if request.method == 'GET' and len(request.GET) > 0:
        search_results = search_movies(request.GET)
        return render(request, 'home.html', context=search_results)

    movie_object = Movie.objects.get(movie_id=movie_id)
    links = OnlineLink.objects.get(movie_id=movie_object.movie_id)

    imdb_link = '0'*(7-len(links.imdb_id))+links.imdb_id
    #poster_link = "{% static \'MLP-20M/" + movie_id +".jpg\' %}"

    movie_detail = {
        'movie': {
            'id': movie_object.movie_id,
            'name': movie_object.title,
            'genres': movie_object.genres,
            'rating': movie_object.rating_mean,
            'liked': movie_object.liked,
            'comparable': movie_object.comparable,
        },
        'links': {
            'imdb': imdb_link,
            'youtube': links.youtube_id,
            'tmdb': links.tmdb_id
        },
        'detail': 'active',
    }
    #movie_detail['poster'] = "{% static 'MLP-20M/" + movie_id +".jpg'%}"
    return render(request, 'movie_detail.html', context=movie_detail)

def rate(request, movie_id):
    movie = Movie.objects.get(pk=movie_id)
    if 'liked' in request.POST:
        movie.liked = 1
    elif 'disliked' in request.POST:
        movie.liked = 0
    elif 'reset' in request.POST:
        movie.liked = None

    movie.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def recommendations(request):
    if request.method == 'GET' and len(request.GET) > 0:
        search_results = search_movies(request.GET)
        return render(request, 'home.html', context=search_results)

    liked, not_liked = load_recommendations()
    context = {
        'recommendations' : 'active',
         'liked': liked,
         'not_liked': not_liked,
    }
    return render(request, 'recommendations.html', context=context)

def about(request):
    context = {
        'about' : 'active',
    }
    return render(request, 'about.html', context=context)
