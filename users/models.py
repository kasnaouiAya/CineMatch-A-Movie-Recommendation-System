from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True
    )
    bio = models.TextField(blank=True, null=True)
    genre_test_done = models.BooleanField(default=False)

    # ← ADD THESE
    following = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='followers',
        blank=True
    )

    def __str__(self):
        return self.username

    def followers_count(self):
        return self.followers.count()

    def following_count(self):
        return self.following.count()