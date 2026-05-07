from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q, Avg, Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Movie, Genre
from reviews.models import Rating, Review, Reply, ReviewLike, ReviewReport, Watchlist
from reviews.forms import ReviewForm
from reviews import models as review_models
from pgvector.django import CosineDistance
from users.models import Notification
import requests

# LOCAL AI IMPORT
from sentence_transformers import SentenceTransformer

local_ai = SentenceTransformer('all-MiniLM-L6-v2')


def _blended_rating(movie):
    """
    Blends TMDB rating (out of 10, scaled to 5) with user ratings.
    - If no user ratings exist: show TMDB rating only.
    - As user ratings accumulate, they gradually take over.
    - After 20 user ratings, it's 100% user-driven.
    """
    tmdb_scaled = (movie.tmdb_rating / 10) * 5

    user_data = Rating.objects.filter(movie=movie).aggregate(
        avg=Avg('score'), count=Count('id')
    )
    user_avg = user_data['avg']
    user_count = user_data['count'] or 0

    if not user_avg:
        return round(tmdb_scaled, 1)

    tmdb_weight = max(0.0, 1 - (user_count / 20))
    user_weight = 1 - tmdb_weight

    blended = (user_avg * user_weight) + (tmdb_scaled * tmdb_weight)
    return round(blended, 1)


def movie_list(request):
    query = request.GET.get('q', '')
    genre_id = request.GET.get('genre', '')
    content_type = request.GET.get('type', '')

    movies = Movie.objects.prefetch_related('genres').all()

    if query:
        movies = movies.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if genre_id:
        movies = movies.filter(genres__id=genre_id)
    if content_type:
        movies = movies.filter(content_type=content_type)

    for movie in movies:
        movie.display_rating = _blended_rating(movie)

    genres = Genre.objects.all()
    return render(request, 'movies/list.html', {
        'movies': movies,
        'genres': genres,
        'query': query,
    })


def trending(request):
    TMDB_API_KEY = '4a997c6df1132cb092a65e07a38fcd77'

    tmdb_popularity = {}
    try:
        for page in range(1, 4):
            url = (
                f'https://api.themoviedb.org/3/discover/movie'
                f'?api_key={TMDB_API_KEY}&language=en-US'
                f'&sort_by=popularity.desc&page={page}'
            )
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                for item in resp.json().get('results', []):
                    tmdb_popularity[item['title']] = item.get('popularity', 0)
    except requests.exceptions.RequestException:
        pass

    movies = (
        Movie.objects
        .prefetch_related('genres')
        .annotate(
            rating_count=Count('ratings', distinct=True),
            review_count=Count('reviews', distinct=True),
            watchlist_count=Count('watchlisted_by', distinct=True),
            avg_score=Avg('ratings__score'),
        )
    )

    scored = []
    for movie in movies:
        user_avg = movie.avg_score or 0
        ratings = movie.rating_count
        reviews = movie.review_count
        watchlist = movie.watchlist_count

        tmdb_scaled = (movie.tmdb_rating / 10) * 5
        if user_avg and ratings > 0:
            tmdb_weight = max(0.0, 1 - (ratings / 20))
            blended_avg = (user_avg * (1 - tmdb_weight)) + (tmdb_scaled * tmdb_weight)
        else:
            blended_avg = tmdb_scaled

        tmdb_pop = tmdb_popularity.get(movie.title, 0)
        tmdb_norm = min(tmdb_pop / 500, 1) * 5

        score = (
            blended_avg * 0.45 +
            ratings     * 0.25 +
            reviews     * 0.15 +
            watchlist   * 0.10 +
            tmdb_norm   * 0.05
        )
        movie.trending_score = round(score, 3)
        movie.avg_score = round(blended_avg, 1)
        scored.append(movie)

    scored.sort(key=lambda m: m.trending_score, reverse=True)

    top_movie = scored[0] if scored else None
    top_3 = scored[1:4] if len(scored) > 1 else []
    rest = scored[4:28] if len(scored) > 4 else []

    return render(request, 'movies/trending.html', {
        'top_movie': top_movie,
        'top_3':     top_3,
        'rest':      rest,
    })


def movie_detail(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        if 'rating_submit' in request.POST and request.user.is_authenticated:
            score = request.POST.get('score')
            if score:
                Rating.objects.update_or_create(
                    user=request.user, movie=movie,
                    defaults={'score': score},
                )
                new_average = _blended_rating(movie)
                movie.average_rating = new_average
                movie.save(update_fields=['average_rating'])
                if is_ajax:
                    return JsonResponse({
                        'status':      'ok',
                        'new_average': new_average,
                        'new_score':   int(score),
                    })

        elif 'review_submit' in request.POST and request.user.is_authenticated:
            body = request.POST.get('body', '').strip()
            is_spoiler = request.POST.get('is_spoiler') == 'on'
            if body:
                review = Review.objects.create(
                    user=request.user, movie=movie,
                    body=body, is_spoiler=is_spoiler,
                )
                if is_ajax:
                    return JsonResponse({
                        'status':     'ok',
                        'id':          review.pk,
                        'username':    request.user.username,
                        'body':        review.body,
                        'is_spoiler': review.is_spoiler,
                        'date':        review.created_at.strftime('%b %d, %Y'),
                    })

        if not is_ajax:
            return redirect('movie_detail', pk=movie.pk)

    user_score = None
    liked_ids = set()
    reported_ids = set()

    if request.user.is_authenticated:
        rating_obj = Rating.objects.filter(user=request.user, movie=movie).first()
        user_score = rating_obj.score if rating_obj else None
        liked_ids = set(ReviewLike.objects.filter(
            user=request.user, review__movie=movie
        ).values_list('review_id', flat=True))
        reported_ids = set(ReviewReport.objects.filter(
            user=request.user, review__movie=movie
        ).values_list('review_id', flat=True))

    reviews = (
        Review.objects
        .filter(movie=movie, is_hidden=False)
        .prefetch_related('likes', 'reports', 'replies__user', 'replies__children')
        .order_by('-created_at')
    )

    average = _blended_rating(movie)
    user_rating_count = Rating.objects.filter(movie=movie).count()
    tmdb_rating_display = round((movie.tmdb_rating / 10) * 5, 1) if movie.tmdb_rating else None

    return render(request, 'movies/detail.html', {
        'movie':               movie,
        'reviews':             reviews,
        'average':             average,
        'review_form':         ReviewForm(),
        'user_score':          user_score,
        'liked_ids':           liked_ids,
        'reported_ids':        reported_ids,
        'user_rating_count':   user_rating_count,
        'tmdb_rating_display': tmdb_rating_display,
    })


@login_required
def toggle_like(request, review_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    review = get_object_or_404(Review, pk=review_id)
    like, created = ReviewLike.objects.get_or_create(user=request.user, review=review)

    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        if review.user != request.user:
            Notification.objects.create(
                recipient=review.user,
                sender=request.user,
                type='like',
                message=f'{request.user.username} liked your review of {review.movie.title}.',
                link=reverse('movie_detail', args=[review.movie.pk]) + f'#review-{review.pk}',
            )

    return JsonResponse({'status': 'ok', 'liked': liked, 'count': review.like_count})


@login_required
def post_reply(request, review_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    review = get_object_or_404(Review, pk=review_id)
    body = request.POST.get('body', '').strip()
    parent_id = request.POST.get('parent_id')
    is_spoiler = request.POST.get('is_spoiler') == 'on'

    if not body:
        return JsonResponse({'error': 'Empty reply'}, status=400)

    parent = None
    if parent_id:
        parent = get_object_or_404(Reply, pk=parent_id)

    reply = Reply.objects.create(
        user=request.user, review=review,
        parent=parent, body=body, is_spoiler=is_spoiler,
    )

    url = reverse('movie_detail', args=[review.movie.pk]) + f'#review-{review.pk}'

    if review.user != request.user:
        Notification.objects.create(
            recipient=review.user,
            sender=request.user,
            type='comment',
            message=f'{request.user.username} commented on your review of {review.movie.title}.',
            link=url,
        )

    if parent and parent.user != request.user and parent.user != review.user:
        Notification.objects.create(
            recipient=parent.user,
            sender=request.user,
            type='comment',
            message=f'{request.user.username} replied to your comment on {review.movie.title}.',
            link=url,
        )

    return JsonResponse({
        'status':     'ok',
        'id':          reply.pk,
        'parent_id':   reply.parent_id,
        'username':    request.user.username,
        'body':        reply.body,
        'is_spoiler': reply.is_spoiler,
        'date':        reply.created_at.strftime('%b %d, %Y'),
    })


@login_required
def report_review(request, review_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    review = get_object_or_404(Review, pk=review_id)

    if ReviewReport.objects.filter(user=request.user, review=review).exists():
        return JsonResponse({'status': 'already_reported'})

    reason = request.POST.get('reason', 'other')
    ReviewReport.objects.create(user=request.user, review=review, reason=reason)

    if review.report_count >= review_models.REPORT_HIDE_THRESHOLD:
        review.is_hidden = True
        review.save(update_fields=['is_hidden'])

    return JsonResponse({'status': 'ok'})


@login_required
def delete_review(request, review_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    review = get_object_or_404(Review, pk=review_id)
    if review.user != request.user and not request.user.is_superuser:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    review.delete()
    return JsonResponse({'status': 'ok'})


@login_required
def delete_reply(request, reply_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    reply = get_object_or_404(Reply, pk=reply_id)
    if reply.user != request.user and not request.user.is_superuser:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    reply.delete()
    return JsonResponse({'status': 'ok'})


def ai_movie_search(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        try:
            query_vector = local_ai.encode(query).tolist()
            results = Movie.objects.annotate(
                distance=CosineDistance('description_vector', query_vector)
            ).order_by('distance')[:12]
        except Exception as e:
            print(f"Local AI Search Error: {e}")
            results = Movie.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )[:12]

    for movie in results:
        movie.display_rating = _blended_rating(movie)

    genres = Genre.objects.all()
    return render(request, 'movies/list.html', {
        'movies': results,
        'genres': genres,
        'query': query,
        'is_ai': True,
    })