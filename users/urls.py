from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('genre-test/', views.genre_test_view, name='genre_test'),
    path('community/', views.community_view, name='community'),
    path('follow/<int:user_id>/', views.follow_view, name='follow'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.other_profile_view, name='profile_by_username'),
    path('lists/create/', views.create_list_view, name='create_list'),
]