from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Avg
from .models import Rating, Review, UserReport
from .forms import RatingForm, ReviewForm
from movies.models import Movie
from django.http import JsonResponse

def movie_reviews(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    if request.method == "POST":

        if "rating_submit" in request.POST:
            rating_value = request.POST.get("score")

            Rating.objects.update_or_create(
                user=request.user,
                movie=movie,
                defaults={"score": rating_value}
            )

        elif "review_submit" in request.POST:
            form = ReviewForm(request.POST)

            if form.is_valid():
                review = form.save(commit=False)
                review.user = request.user
                review.movie = movie
                review.save()

        return redirect("movie_reviews", movie_id=movie.id)

    reviews = Review.objects.filter(movie=movie)
    average = Rating.objects.filter(movie=movie).aggregate(
        Avg("score")
    )["score__avg"] or 0

    return render(request, "reviews/movie_reviews.html", {
        "movie": movie,
        "reviews": reviews,
        "average": average,
        "review_form": ReviewForm()
    })
    


def report_review(request, review_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    review = get_object_or_404(Review, pk=review_id)
    reason = request.POST.get('reason', 'SPAM')
    
    # 1. Créer le signalement
    report, created = UserReport.objects.get_or_create(
        review=review, 
        reporter=request.user,
        defaults={'reason': reason}
    )

    if not created:
        return JsonResponse({'message': 'Already reported'}, status=400)

    # 2. Logique de modération
    author = review.user
    report_count = review.user_content_reports.count()

    # CAS A : Harcèlement (Suppression immédiate du compte)
    if reason == 'HARASSMENT':
        author.delete() 
        return JsonResponse({'message': 'User banned for harassment'})

    # CAS B : Plus de 3 signalements (Suppression du compte)
    if report_count >= 3:
        author.delete()
        return JsonResponse({'message': 'User deleted due to multiple reports'})

    # CAS C : 1er signalement (Notification - ici on peut envoyer un mail ou un message system)
    if report_count == 1:
        # Code pour envoyer une notification (ex: author.profile.add_warning())
        pass

    return JsonResponse({'message': 'Report submitted'})