from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('genre-test/', views.genre_test_view, name='genre_test'),
    path('profile/', views.profile_view, name='profile'),
]
