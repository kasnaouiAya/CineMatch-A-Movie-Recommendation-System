from django.db import models
from pgvector.django import VectorField
from django.conf import settings

from users.models import User

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    CONTENT_TYPES = [
        ('movie', 'Movie'),
        ('series', 'Series'),
        ('documentary', 'Documentary'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    release_year = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)
    language = models.CharField(max_length=50, blank=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES, default='movie')
    poster = models.ImageField(upload_to='posters/', blank=True, null=True)
    trailer_url = models.URLField(blank=True)
    genres = models.ManyToManyField(Genre, related_name='movies', blank=True)
    poster_path = models.CharField(max_length=255, blank=True, null=True)
    average_rating = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    description_vector = VectorField(dimensions=384, null=True, blank=True)
    tmdb_rating = models.FloatField(default=0.0)
    
    def __str__(self):
        return f'{self.title} ({self.release_year})'

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE, related_name='in_watchlist')
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'movie']

class Watched(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watched_movies')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    watched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')

class MovieList(models.Model):
    LIST_TYPES = [
        ('custom', 'Custom'),
        ('favorites', 'Favorites'),
        ('must_watch', 'Must Watch'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='movie_lists'
    )
    name = models.CharField(max_length=100)
    list_type = models.CharField(max_length=20, choices=LIST_TYPES, default='custom')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'list_type'],
                condition=models.Q(list_type__in=['favorites', 'must_watch']),
                name='unique_default_lists_per_user'
            )
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def movie_count(self):
        return self.movies.count()


class MovieListItem(models.Model):
    movie_list = models.ForeignKey(
        MovieList,
        on_delete=models.CASCADE,
        related_name='movies'
    )
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['movie_list', 'movie']