from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import User, Notification

# ── Follow ──
@receiver(m2m_changed, sender=User.following.through)
def notify_follow(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        for user_id in pk_set:
            target = User.objects.get(pk=user_id)
            Notification.objects.create(
                recipient=target,
                sender=instance,
                type='follow',
                message=f'{instance.username} started following you.',
            )