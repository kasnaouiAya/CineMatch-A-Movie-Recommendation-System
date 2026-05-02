from django.db import models
from django.conf import settings


class Rating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings')
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE, related_name='ratings')
    score = models.IntegerField()  # 1 to 5
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f'{self.user.username} → {self.movie.title}: {self.score}/5'


class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE, related_name='reviews')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f'{self.user.username} review of {self.movie.title}'


# class Watchlist(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='watchlist')
#     movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE, related_name='watchlisted_by')
#     watched = models.BooleanField(default=False)
#     added_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('user', 'movie')

#     def __str__(self):
#         return f'{self.user.username} — {self.movie.title}'