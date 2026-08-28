import redis
from django.conf import settings
from .models import Post, Follow

FEED_LIMIT = 500

def get_redis_client():
    """Returns a direct Redis client using the configured URL."""
    redis_url = getattr(settings, "CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
    return redis.from_url(redis_url, decode_responses=True)

def feed_key(user_id):
    return f"feed:{user_id}"

def push_post_to_feed(user_id, post_id):
    """Pushes a post ID to the top of a user's feed list and trims to FEED_LIMIT."""
    r = get_redis_client()
    key = feed_key(user_id)
    r.lpush(key, post_id)
    r.ltrim(key, 0, FEED_LIMIT - 1)

def remove_post_from_feed(user_id, post_id):
    """Removes a specific post ID from a user's feed list."""
    r = get_redis_client()
    r.lrem(feed_key(user_id), 0, post_id)

def add_user_posts_to_feed(follower_id, following_id):
    """
    When a user follows someone, fetch their recent posts and add them 
    to the follower's feed, maintaining order.
    """
    recent_posts = Post.objects.filter(user_id=following_id).order_by("created_at")[:100]
    if not recent_posts:
        return
        
    r = get_redis_client()
    key = feed_key(follower_id)
    # LPUSH from oldest to newest so newest ends up on top
    for p in recent_posts:
        r.lpush(key, p.id)
    r.ltrim(key, 0, FEED_LIMIT - 1)

def remove_user_posts_from_feed(follower_id, following_id):
    """When a user unfollows someone, remove all their posts from the feed."""
    post_ids = list(Post.objects.filter(user_id=following_id).values_list("id", flat=True))
    if not post_ids:
        return
        
    r = get_redis_client()
    key = feed_key(follower_id)
    # LREM each post ID
    for pid in post_ids:
        r.lrem(key, 0, pid)

def get_feed_post_ids(user_id, offset=0, limit=10):
    """
    Fetch a page of post IDs from the user's Redis feed.
    If the feed doesn't exist (e.g. empty or expired), fallback to DB.
    """
    r = get_redis_client()
    key = feed_key(user_id)
    
    # Check if feed exists
    if not r.exists(key):
        return rebuild_feed_for_user(user_id, offset, limit)
        
    # Fetch from Redis
    end = offset + limit - 1
    post_ids = r.lrange(key, offset, end)
    
    if not post_ids:
        return []
        
    # Convert string IDs to integers
    return [int(pid) for pid in post_ids]

def rebuild_feed_for_user(user_id, offset=0, limit=10):
    """
    Fallback mechanism: rebuild the feed cache from the database.
    """
    following_ids = Follow.objects.filter(follower_id=user_id).values_list("following_id", flat=True)
    if not following_ids:
        return []
        
    # Fetch top 500 recent posts
    recent_posts = (
        Post.objects.filter(user_id__in=following_ids)
        .order_by("-created_at")
        .values_list("id", flat=True)[:FEED_LIMIT]
    )
    
    if not recent_posts:
        return []
        
    r = get_redis_client()
    key = feed_key(user_id)
    
    # Push all 500 posts to Redis
    # We reverse because we want the newest (index 0) to be LPUSH'd last
    for pid in reversed(recent_posts):
        r.lpush(key, pid)
        
    # Set expiration so we don't hold inactive user feeds forever (e.g., 7 days)
    r.expire(key, 604800)
    
    end = offset + limit
    return list(recent_posts)[offset:end]
