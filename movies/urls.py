from django.urls import path
from . import views

urlpatterns = [
    # Movie list and detail views
    path('', views.movie_list, name='movie_list'),
    path('<int:pk>/', views.movie_detail, name='movie_detail'),
]