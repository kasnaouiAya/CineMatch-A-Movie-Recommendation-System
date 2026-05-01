from django.urls import path
from . import views

urlpatterns = [
    path('',                                    views.movie_list,    name='movie_list'),
    path('trending/',                           views.trending,      name='trending'),
    path('<int:pk>/',                           views.movie_detail,  name='movie_detail'),
    path('review/<int:review_id>/like/',        views.toggle_like,   name='toggle_like'),
    path('review/<int:review_id>/reply/',       views.post_reply,    name='post_reply'),
    path('review/<int:review_id>/report/',      views.report_review, name='report_review'),
    path('review/<int:review_id>/delete/',      views.delete_review, name='delete_review'),
    path('reply/<int:reply_id>/delete/',        views.delete_reply,  name='delete_reply'),
    path('ai-search/',                          views.ai_movie_search, name='ai_movie_search'),
]