
from django.db import models


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
    average_rating = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.title} ({self.release_year})'