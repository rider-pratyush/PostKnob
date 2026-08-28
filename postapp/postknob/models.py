"""
PostKnob models.

Models:
- Post        — a social media post with text, optional photo, hashtags
- Profile     — extended user profile (bio, avatar, website, location)
- Follow      — directional follow relationship between users
- Like        — user ↔ post like
- Comment     — user comment on a post
- Bookmark    — user saves a post
- Hashtag     — topic tags extracted from post text
"""
from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify


# ---------------------------------------------------------------------------
# Hashtag
# ---------------------------------------------------------------------------

class Hashtag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["slug"])]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"#{self.name}"


# ---------------------------------------------------------------------------
# Post
# ---------------------------------------------------------------------------

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    text = models.TextField(max_length=1000)
    photo = models.ImageField(upload_to="photos/", blank=True, null=True)
    hashtags = models.ManyToManyField(Hashtag, blank=True, related_name="posts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} – {self.text[:40]}"

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def comment_count(self):
        return self.comments.count()


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    # Keep backward-compat field used in existing templates
    avatar_url = models.URLField(default="", blank=True)

    class Meta:
        indexes = [models.Index(fields=["user"])]

    def __str__(self):
        return self.user.username

    def get_avatar(self):
        """Return avatar URL, preferring uploaded file over external URL."""
        if self.avatar and hasattr(self.avatar, "url"):
            return self.avatar.url
        if self.avatar_url:
            return self.avatar_url
        return "https://ui-avatars.com/api/?name={}&background=1a1a2e&color=FFD700&bold=true".format(
            self.user.username
        )


# ---------------------------------------------------------------------------
# Follow
# ---------------------------------------------------------------------------

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("follower", "following")
        indexes = [
            models.Index(fields=["follower"]),
            models.Index(fields=["following"]),
        ]

    def __str__(self):
        return f"{self.follower.username} → {self.following.username}"


# ---------------------------------------------------------------------------
# Like
# ---------------------------------------------------------------------------

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")
        indexes = [models.Index(fields=["post"])]

    def __str__(self):
        return f"{self.user.username} ♥ Post#{self.post_id}"


# ---------------------------------------------------------------------------
# Comment
# ---------------------------------------------------------------------------

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["post", "created_at"])]

    def __str__(self):
        return f"{self.user.username} on Post#{self.post_id}: {self.body[:30]}"


# ---------------------------------------------------------------------------
# Bookmark
# ---------------------------------------------------------------------------

class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookmarks")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return f"{self.user.username} 🔖 Post#{self.post_id}"