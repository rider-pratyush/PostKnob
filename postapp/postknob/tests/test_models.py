"""
Model tests: creation, str representation, signals, indexes, constraints.
"""
import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError

from postknob.models import Bookmark, Comment, Follow, Hashtag, Like, Post, Profile
from .factories import (
    BookmarkFactory,
    CommentFactory,
    FollowFactory,
    HashtagFactory,
    LikeFactory,
    PostFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestProfileSignal:
    def test_profile_created_on_user_create(self):
        user = UserFactory()
        assert Profile.objects.filter(user=user).exists()

    def test_profile_str(self):
        user = UserFactory(username="alice")
        assert str(user.profile) == "alice"


@pytest.mark.django_db
class TestPostModel:
    def test_post_str(self):
        post = PostFactory(text="Hello world this is a post")
        assert "Hello world" in str(post)

    def test_post_like_count(self):
        post = PostFactory()
        assert post.like_count == 0
        LikeFactory(post=post)
        post.refresh_from_db()
        assert post.like_count == 1

    def test_post_comment_count(self):
        post = PostFactory()
        CommentFactory(post=post)
        CommentFactory(post=post)
        assert post.comment_count == 2

    def test_post_ordering(self):
        p1 = PostFactory()
        p2 = PostFactory()
        posts = list(Post.objects.all())
        assert posts[0] == p2  # newest first


@pytest.mark.django_db
class TestHashtag:
    def test_hashtag_slug_auto(self):
        tag = HashtagFactory(name="python programming")
        assert tag.slug == "python-programming"

    def test_hashtag_str(self):
        tag = HashtagFactory(name="django")
        assert str(tag) == "#django"


@pytest.mark.django_db
class TestFollow:
    def test_follow_str(self):
        follow = FollowFactory()
        assert "→" in str(follow)

    def test_unique_follow(self):
        f = FollowFactory()
        with pytest.raises(IntegrityError):
            FollowFactory(follower=f.follower, following=f.following)


@pytest.mark.django_db
class TestLike:
    def test_unique_like(self):
        like = LikeFactory()
        with pytest.raises(IntegrityError):
            LikeFactory(user=like.user, post=like.post)


@pytest.mark.django_db
class TestComment:
    def test_comment_str(self):
        comment = CommentFactory(body="Great post!")
        assert "Great post!" in str(comment)


@pytest.mark.django_db
class TestBookmark:
    def test_unique_bookmark(self):
        bm = BookmarkFactory()
        with pytest.raises(IntegrityError):
            BookmarkFactory(user=bm.user, post=bm.post)
