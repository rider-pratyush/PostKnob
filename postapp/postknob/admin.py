from django.contrib import admin

from .models import Bookmark, Comment, Follow, Hashtag, Like, Post, Profile


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "text_preview", "like_count", "comment_count", "created_at"]
    list_filter = ["created_at", "hashtags"]
    search_fields = ["user__username", "text"]
    date_hierarchy = "created_at"
    raw_id_fields = ["user"]
    filter_horizontal = ["hashtags"]

    def text_preview(self, obj):
        return obj.text[:60]
    text_preview.short_description = "Text"

    def like_count(self, obj):
        return obj.likes.count()

    def comment_count(self, obj):
        return obj.comments.count()


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "location", "website"]
    search_fields = ["user__username", "bio", "location"]
    raw_id_fields = ["user"]


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ["follower", "following", "created_at"]
    search_fields = ["follower__username", "following__username"]
    raw_id_fields = ["follower", "following"]


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ["user", "post", "created_at"]
    raw_id_fields = ["user", "post"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["user", "post", "body_preview", "created_at"]
    search_fields = ["user__username", "body"]
    raw_id_fields = ["user", "post"]

    def body_preview(self, obj):
        return obj.body[:50]
    body_preview.short_description = "Comment"


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ["user", "post", "created_at"]
    raw_id_fields = ["user", "post"]


@admin.register(Hashtag)
class HashtagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "post_count"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ["name"]}

    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = "Posts"
