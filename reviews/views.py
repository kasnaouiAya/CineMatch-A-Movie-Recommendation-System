from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Avg
from .models import Rating, Review
from .forms import RatingForm, ReviewForm
from movies.models import Movie

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