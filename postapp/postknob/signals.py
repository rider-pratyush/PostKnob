from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile


@receiver(post_save, sender=User)
def create_or_save_profile(sender, instance, created, **kwargs):
    """Ensure every User always has an associated Profile."""
    if created:
        Profile.objects.create(user=instance)
    else:
        # Save profile in case it was updated via user save
        Profile.objects.get_or_create(user=instance)

from django.db.models.signals import post_delete
from .models import Post
from .tasks import fanout_new_post, remove_post_from_all_feeds

@receiver(post_save, sender=Post)
def post_saved(sender, instance, created, **kwargs):
    if created:
        fanout_new_post.delay(instance.id)

@receiver(post_delete, sender=Post)
def post_deleted(sender, instance, **kwargs):
    remove_post_from_all_feeds.delay(instance.id, instance.user_id)
