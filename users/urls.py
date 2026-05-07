from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('genre-test/', views.genre_test_view, name='genre_test'),
    path('profile/', views.profile_view, name='profile'),

    path('profile/<str:username>/', views.other_profile_view, name='profile_by_username'),

    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/mark-read/', views.mark_all_read, name='mark_all_read'),

    path('list/create/', views.create_list, name='create_list'),
    path('list/delete/<int:list_id>/', views.delete_list, name='delete_list'),

    path('watch-later/add/<int:movie_id>/', views.add_to_watch_later, name='add_to_watch_later'),
    path('watch-later/remove/<int:movie_id>/', views.remove_from_watch_later, name='remove_from_watch_later'),

    path('watched/add/<int:movie_id>/', views.add_to_watched, name='add_to_watched'),
    path('watched/remove/<int:movie_id>/', views.remove_from_watched, name='remove_from_watched'),

    path('follow/<int:user_id>/', views.follow_view, name='follow'),
    path('community/', views.community_view, name='community'),

    path('user/<str:username>/', views.other_profile_view, name='other_profile'),

    path('watchlist/', views.watchlist_view, name='watchlist'),
    path('watched/', views.watched_view, name='watched'),

    path('dashboard/users/', views.user_list_view, name='user-list'),
    path('dashboard/users/delete/<int:user_id>/', views.delete_user, name='delete-user'),
    path('dashboard/users/edit/<int:user_id>/', views.edit_user_view, name='edit-user'),
    path('dashboard/users/add/', views.admin_add_user, name='admin-add-user'),

]