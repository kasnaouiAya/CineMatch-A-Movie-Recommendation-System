
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q, Avg
from .models import Movie, Genre
from reviews.models import Rating, Review
from reviews.forms import ReviewForm


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
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':

        if 'rating_submit' in request.POST and request.user.is_authenticated:
            score = request.POST.get('score')
            if score:
                already_rated = Rating.objects.filter(
                    user=request.user, movie=movie
                ).exists()

                if already_rated:
                    if is_ajax:
                        return JsonResponse({'status': 'already_rated'})
                else:
                    Rating.objects.create(
                        user=request.user,
                        movie=movie,
                        score=score,
                    )
                    new_average = Rating.objects.filter(movie=movie).aggregate(
                        avg=Avg('score')
                    )['avg'] or 0

                    if is_ajax:
                        return JsonResponse({
                            'status': 'ok',
                            'new_average': round(float(new_average), 1),
                        })

        elif 'review_submit' in request.POST and request.user.is_authenticated:
            already_reviewed = Review.objects.filter(
                user=request.user, movie=movie
            ).exists()

            if already_reviewed:
                if is_ajax:
                    return JsonResponse({'status': 'already_reviewed'})
            else:
                form = ReviewForm(request.POST)
                if form.is_valid():
                    review = form.save(commit=False)
                    review.user = request.user
                    review.movie = movie
                    review.save()
                    if is_ajax:
                        return JsonResponse({'status': 'ok'})

        return redirect('movie_detail', pk=movie.pk)

    # GET
    already_rated = (
        request.user.is_authenticated and
        Rating.objects.filter(user=request.user, movie=movie).exists()
    )
    user_score = None
    if already_rated:
        user_score = Rating.objects.get(user=request.user, movie=movie).score

    reviews = Review.objects.filter(movie=movie).order_by('-created_at')
    average = Rating.objects.filter(movie=movie).aggregate(
        avg=Avg('score')
    )['avg'] or 0

    return render(request, 'movies/detail.html', {
        'movie': movie,
        'reviews': reviews,
        'average': average,
        'review_form': ReviewForm(),
        'already_rated': already_rated,
        'user_score': user_score,
    })
