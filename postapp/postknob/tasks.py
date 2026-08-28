"""
PostKnob Celery tasks.
"""
from __future__ import annotations

import logging

from celery import shared_task
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_follow_notification(self, follower_id: int, following_id: int):
    """Notify a user that they have a new follower."""
    try:
        follower = User.objects.get(pk=follower_id)
        following = User.objects.get(pk=following_id)
        # In production, replace with actual email/push notification
        logger.info("📣 %s followed %s", follower.username, following.username)
        # Example: send_mail(subject=..., message=..., from_email=..., recipient_list=[following.email])
    except User.DoesNotExist as exc:
        logger.warning("send_follow_notification: user not found — %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_post_image(self, post_id: int):
    """Resize and optimise a post's uploaded image."""
    try:
        from postknob.models import Post
        from PIL import Image

        post = Post.objects.get(pk=post_id)
        if not post.photo:
            return
        img_path = post.photo.path
        with Image.open(img_path) as img:
            img = img.convert("RGB")
            max_size = (1200, 1200)
            img.thumbnail(max_size, Image.LANCZOS)
            img.save(img_path, optimize=True, quality=85)
        logger.info("✅ Optimised image for post #%d", post_id)
    except Exception as exc:
        logger.error("process_post_image failed for #%d: %s", post_id, exc)
        raise self.retry(exc=exc)


@shared_task
def cleanup_old_notifications():
    """Periodic task: purge stale data if needed. Runs via Celery Beat."""
    logger.info("🧹 cleanup_old_notifications ran — no-op placeholder")


@shared_task
def fanout_new_post(post_id):
    """Fan-out on Write: push a new post to all followers' feeds."""
    from postknob.models import Follow, Post
    from postknob.services import push_post_to_feed

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return f"Post {post_id} not found."

    author_id = post.user_id
    follower_ids = Follow.objects.filter(following_id=author_id).values_list("follower_id", flat=True)
    
    count = 0
    for follower_id in follower_ids:
        push_post_to_feed(follower_id, post_id)
        count += 1
        
    return f"Pushed post {post_id} to {count} feeds."

@shared_task
def remove_post_from_all_feeds(post_id, author_id):
    """Fan-out on Delete: remove a deleted post from all followers' feeds."""
    from postknob.models import Follow
    from postknob.services import remove_post_from_feed

    follower_ids = Follow.objects.filter(following_id=author_id).values_list("follower_id", flat=True)
    
    count = 0
    for follower_id in follower_ids:
        remove_post_from_feed(follower_id, post_id)
        count += 1
        
    return f"Removed post {post_id} from {count} feeds."

@shared_task
def process_follow_feed(follower_id, following_id):
    """Populate feed when a user follows someone."""
    from postknob.services import add_user_posts_to_feed
    add_user_posts_to_feed(follower_id, following_id)
    return f"Added user {following_id} posts to {follower_id} feed."

@shared_task
def process_unfollow_feed(follower_id, following_id):
    """Remove feed items when a user unfollows someone."""
    from postknob.services import remove_user_posts_from_feed
    remove_user_posts_from_feed(follower_id, following_id)
    return f"Removed user {following_id} posts from {follower_id} feed."
