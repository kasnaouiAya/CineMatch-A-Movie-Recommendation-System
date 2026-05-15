from django.contrib import admin
# This file is used to register  models with the Django admin site.
from .models import Movie, Genre

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'content_type', 'release_year', 'average_rating']
    list_filter = ['content_type', 'genres']
    search_fields = ['title']
    filter_horizontal = ['genres']

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    pass
