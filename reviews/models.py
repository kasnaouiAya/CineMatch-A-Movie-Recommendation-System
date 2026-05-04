from django.db import models
from django.conf import settings

REPORT_HIDE_THRESHOLD = 3   # hide a review after this many reports


class Rating(models.Model):
    user  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings')
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE, related_name='ratings')
    score = models.IntegerField()          # 1–5
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f'{self.user.username} → {self.movie.title}: {self.score}/5'


class Review(models.Model):
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    movie      = models.ForeignKey('movies.Movie', on_delete=models.CASCADE, related_name='reviews')
    body       = models.TextField()
    is_spoiler = models.BooleanField(default=False)
    is_hidden  = models.BooleanField(default=False)   # auto-hidden after report threshold
    created_at = models.DateTimeField(auto_now_add=True)

    # No unique_together — users can post multiple reviews

    def __str__(self):
        return f'{self.user.username} review of {self.movie.title}'

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def report_count(self):
        return self.reports.count()


class Reply(models.Model):
    """Self-referential model supporting unlimited nesting depth."""
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='replies')
    review     = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='replies')
    parent     = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    body       = models.TextField()
    is_spoiler = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} reply on review #{self.review_id}'


class ReviewLike(models.Model):
    user   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_likes')
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'review')

    def __str__(self):
        return f'{self.user.username} likes review #{self.review_id}'


class ReviewReport(models.Model):
    REASONS = [
        ('spam',       'Spam'),
        ('spoiler',    'Unmarked spoiler'),
        ('hate',       'Hate speech'),
        ('harassment', 'Harassment'),
        ('other',      'Other'),
    ]
    user   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_reports')
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='reports')
    reason = models.CharField(max_length=20, choices=REASONS, default='other')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'review')   # one report per user per review

    def __str__(self):
        return f'{self.user.username} reported review #{self.review_id} ({self.reason})'


class Watchlist(models.Model):
    user     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='watchlist')
    movie    = models.ForeignKey('movies.Movie', on_delete=models.CASCADE, related_name='watchlisted_by')
    watched  = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f'{self.user.username} — {self.movie.title}'