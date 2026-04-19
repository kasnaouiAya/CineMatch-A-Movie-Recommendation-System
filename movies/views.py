from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.db.models import Q
from .models import Movie, Genre

def movie_list(request):
    query = request.GET.get('q', '')
    genre_id = request.GET.get('genre', '')
    content_type = request.GET.get('type', '')

    movies = Movie.objects.prefetch_related('genres').all()

    if query:
        movies = movies.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
    if genre_id:
        movies = movies.filter(genres__id=genre_id)
    if content_type:
        movies = movies.filter(content_type=content_type)

    genres = Genre.objects.all()
    return render(request, 'movies/list.html', {
        'movies': movies,
        'genres': genres,
        'query': query,
    })

def movie_detail(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    return render(request, 'movies/detail.html', {'movie': movie})