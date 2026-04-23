from django.urls import path
from . import views

urlpatterns = [
    path("<int:movie_id>/", views.movie_reviews, name="movie_reviews"),
]
