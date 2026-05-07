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
    

class Notification(models.Model):
    TYPES = [
        ('follow',  'Follow'),
        ('like',    'Like'),
        ('comment', 'Comment'),
    ]
    recipient  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    type       = models.CharField(max_length=20, choices=TYPES)
    message    = models.TextField()
    is_read    = models.BooleanField(default=False)
    link       = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']