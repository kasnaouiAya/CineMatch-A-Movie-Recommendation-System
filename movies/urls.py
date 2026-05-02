from django.urls import path
from . import views

urlpatterns = [
    path('', views.movie_list, name='movie_list'),
    path('<int:pk>/', views.movie_detail, name='movie_detail'),
    path('<int:pk>/watchlist/', views.toggle_watchlist, name='toggle_watchlist'),
    path('<int:pk>/watched/', views.toggle_watched, name='toggle_watched'),
    path('watchlist/', views.watchlist_view, name='watchlist'),
    path('watched/', views.watched_view, name='watched'),
]