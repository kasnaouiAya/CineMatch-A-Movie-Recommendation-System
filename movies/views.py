from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q, Avg
from django.contrib.auth.decorators import login_required
from .models import Movie, Genre
from reviews.models import Rating, Review, Reply, ReviewLike, ReviewReport
from reviews.forms import ReviewForm
from reviews import models as review_models


def movie_list(request):
    query      = request.GET.get('q', '')
    genre_id   = request.GET.get('genre', '')
    content_type = request.GET.get('type', '')

    movies = Movie.objects.prefetch_related('genres').all()

    if query:
        movies = movies.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if genre_id:
        movies = movies.filter(genres__id=genre_id)
    if content_type:
        movies = movies.filter(content_type=content_type)

    genres = Genre.objects.all()
    return render(request, 'movies/list.html', {
        'movies': movies,
        'genres': genres,
        'query':  query,
    })


def movie_detail(request, pk):
    movie   = get_object_or_404(Movie, pk=pk)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':

        # ── RATING ──────────────────────────────────────────────────────────
        if 'rating_submit' in request.POST and request.user.is_authenticated:
            score = request.POST.get('score')
            if score:
                Rating.objects.update_or_create(
                    user=request.user, movie=movie,
                    defaults={'score': score},
                )
                new_average = Rating.objects.filter(movie=movie).aggregate(
                    avg=Avg('score')
                )['avg'] or 0
                if is_ajax:
                    return JsonResponse({
                        'status':      'ok',
                        'new_average': round(float(new_average), 1),
                        'new_score':   int(score),
                    })

        # ── REVIEW ──────────────────────────────────────────────────────────
        elif 'review_submit' in request.POST and request.user.is_authenticated:
            body       = request.POST.get('body', '').strip()
            is_spoiler = request.POST.get('is_spoiler') == 'on'
            if body:
                review = Review.objects.create(
                    user=request.user, movie=movie,
                    body=body, is_spoiler=is_spoiler,
                )
                if is_ajax:
                    return JsonResponse({
                        'status':     'ok',
                        'id':         review.pk,
                        'username':   request.user.username,
                        'body':       review.body,
                        'is_spoiler': review.is_spoiler,
                        'date':       review.created_at.strftime('%b %d, %Y'),
                    })

        if not is_ajax:
            return redirect('movie_detail', pk=movie.pk)

    # ── GET ──────────────────────────────────────────────────────────────────
    user_score = None
    liked_ids  = set()
    reported_ids = set()

    if request.user.is_authenticated:
        rating_obj = Rating.objects.filter(user=request.user, movie=movie).first()
        user_score = rating_obj.score if rating_obj else None
        liked_ids    = set(ReviewLike.objects.filter(
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
    average = Rating.objects.filter(movie=movie).aggregate(avg=Avg('score'))['avg'] or 0

    return render(request, 'movies/detail.html', {
        'movie':        movie,
        'reviews':      reviews,
        'average':      average,
        'review_form':  ReviewForm(),
        'user_score':   user_score,
        'liked_ids':    liked_ids,
        'reported_ids': reported_ids,
    })


# ── LIKE TOGGLE ─────────────────────────────────────────────────────────────
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
    return JsonResponse({'status': 'ok', 'liked': liked, 'count': review.like_count})


# ── REPLY ────────────────────────────────────────────────────────────────────
@login_required
def post_reply(request, review_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    review    = get_object_or_404(Review, pk=review_id)
    body      = request.POST.get('body', '').strip()
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
    return JsonResponse({
        'status':     'ok',
        'id':         reply.pk,
        'parent_id':  reply.parent_id,
        'username':   request.user.username,
        'body':       reply.body,
        'is_spoiler': reply.is_spoiler,
        'date':       reply.created_at.strftime('%b %d, %Y'),
    })


# ── REPORT ───────────────────────────────────────────────────────────────────
@login_required
def report_review(request, review_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    review = get_object_or_404(Review, pk=review_id)

    if ReviewReport.objects.filter(user=request.user, review=review).exists():
        return JsonResponse({'status': 'already_reported'})

    reason = request.POST.get('reason', 'other')
    ReviewReport.objects.create(user=request.user, review=review, reason=reason)

    # auto-hide after threshold
    if review.report_count >= review_models.REPORT_HIDE_THRESHOLD:
        review.is_hidden = True
        review.save(update_fields=['is_hidden'])

    return JsonResponse({'status': 'ok'})


# ── DELETE REVIEW ─────────────────────────────────────────────────────────────
@login_required
def delete_review(request, review_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    review = get_object_or_404(Review, pk=review_id)
    if review.user != request.user and not request.user.is_superuser:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    review.delete()
    return JsonResponse({'status': 'ok'})


# ── DELETE REPLY ──────────────────────────────────────────────────────────────
@login_required
def delete_reply(request, reply_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    reply = get_object_or_404(Reply, pk=reply_id)
    if reply.user != request.user and not request.user.is_superuser:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    reply.delete()
    return JsonResponse({'status': 'ok'})