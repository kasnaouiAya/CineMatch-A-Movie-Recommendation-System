from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    genre_test_done = models.BooleanField(default=False)
    favorite_genres = models.JSONField(default=list, blank=True)

    following = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='followers',
        blank=True
    )

    def is_following(self, user):
        return self.following.filter(id=user.id).exists()

    def get_followers_count(self):
        return self.followers.count()

    def get_following_count(self):
        return self.following.count()

    def __str__(self):
        return self.username


class List(models.Model):
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='lists'
    )
    name = models.CharField(max_length=150)
    movies = models.ManyToManyField('movies.Movie', blank=True, related_name='in_lists')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.name}'