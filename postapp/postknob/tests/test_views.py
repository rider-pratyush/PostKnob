"""
View tests: CRUD, permissions, profile, follow, feed, search, bookmarks.
"""
import pytest
from django.urls import reverse

from postknob.models import Bookmark, Comment, Follow, Like, Post
from .factories import BookmarkFactory, CommentFactory, FollowFactory, LikeFactory, PostFactory, UserFactory


@pytest.mark.django_db
class TestHomePage:
    def test_home_status_200(self, client):
        response = client.get(reverse("home"))
        assert response.status_code == 200

    def test_home_context(self, client):
        PostFactory()
        response = client.get(reverse("home"))
        assert "trending_posts" in response.context


@pytest.mark.django_db
class TestPostCRUD:
    def test_tweet_list_public(self, client):
        PostFactory.create_batch(3)
        response = client.get(reverse("postknob:tweet_list"))
        assert response.status_code == 200
        assert len(response.context["tweets"]) == 3

    def test_tweet_detail_public(self, client):
        post = PostFactory()
        response = client.get(reverse("postknob:tweet_detail", kwargs={"pk": post.pk}))
        assert response.status_code == 200
        assert response.context["tweet"] == post

    def test_create_post_requires_login(self, client):
        response = client.post(reverse("postknob:tweet_create"), {"text": "hello"})
        assert response.status_code == 302
        assert "/accounts/login" in response.url or "login" in response.url

    def test_create_post_authenticated(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.post(reverse("postknob:tweet_create"), {"text": "Hello PostKnob!"})
        assert response.status_code == 302
        assert Post.objects.filter(user=user, text="Hello PostKnob!").exists()

    def test_edit_own_post(self, client):
        user = UserFactory()
        post = PostFactory(user=user)
        client.force_login(user)
        response = client.post(
            reverse("postknob:tweet_edit", kwargs={"tweet_id": post.pk}),
            {"text": "Updated text"}
        )
        assert response.status_code == 302
        post.refresh_from_db()
        assert post.text == "Updated text"

    def test_edit_other_user_post_forbidden(self, client):
        owner = UserFactory()
        attacker = UserFactory()
        post = PostFactory(user=owner)
        client.force_login(attacker)
        response = client.post(
            reverse("postknob:tweet_edit", kwargs={"tweet_id": post.pk}),
            {"text": "Hacked!"}
        )
        assert response.status_code == 404

    def test_delete_own_post(self, client):
        user = UserFactory()
        post = PostFactory(user=user)
        client.force_login(user)
        client.post(reverse("postknob:tweet_delete", kwargs={"tweet_id": post.pk}))
        assert not Post.objects.filter(pk=post.pk).exists()

    def test_delete_other_user_post_forbidden(self, client):
        owner = UserFactory()
        attacker = UserFactory()
        post = PostFactory(user=owner)
        client.force_login(attacker)
        response = client.post(reverse("postknob:tweet_delete", kwargs={"tweet_id": post.pk}))
        assert response.status_code == 404
        assert Post.objects.filter(pk=post.pk).exists()


@pytest.mark.django_db
class TestSearch:
    def test_search_by_text(self, client):
        PostFactory(text="django is great")
        PostFactory(text="python rocks")
        response = client.get(reverse("postknob:tweet_list") + "?q=django")
        assert response.status_code == 200
        assert response.context["tweets"].paginator.count == 1


@pytest.mark.django_db
class TestProfile:
    def test_profile_view(self, client):
        user = UserFactory()
        response = client.get(reverse("postknob:profile", kwargs={"username": user.username}))
        assert response.status_code == 200
        assert response.context["profile_user"] == user

    def test_profile_edit_requires_login(self, client):
        response = client.get(reverse("postknob:profile_edit"))
        assert response.status_code == 302

    def test_profile_edit_saves(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.post(reverse("postknob:profile_edit"), {
            "bio": "I am a hobnobber",
            "website": "https://example.com",
            "location": "Mumbai",
        })
        assert response.status_code == 302
        user.profile.refresh_from_db()
        assert user.profile.bio == "I am a hobnobber"


@pytest.mark.django_db
class TestFollowToggle:
    def test_follow_user(self, client):
        user = UserFactory()
        target = UserFactory()
        client.force_login(user)
        response = client.post(
            reverse("postknob:follow_toggle", kwargs={"username": target.username}),
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert Follow.objects.filter(follower=user, following=target).exists()

    def test_unfollow_user(self, client):
        user = UserFactory()
        target = UserFactory()
        FollowFactory(follower=user, following=target)
        client.force_login(user)
        client.post(
            reverse("postknob:follow_toggle", kwargs={"username": target.username}),
            HTTP_HX_REQUEST="true",
        )
        assert not Follow.objects.filter(follower=user, following=target).exists()

    def test_cannot_follow_self(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.post(
            reverse("postknob:follow_toggle", kwargs={"username": user.username}),
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestFeed:
    def test_feed_requires_login(self, client):
        response = client.get(reverse("postknob:feed"))
        assert response.status_code == 302

    def test_feed_shows_followed_posts(self, client):
        user = UserFactory()
        followed = UserFactory()
        FollowFactory(follower=user, following=followed)
        post = PostFactory(user=followed)
        other_post = PostFactory()  # from a non-followed user
        client.force_login(user)
        response = client.get(reverse("postknob:feed"))
        assert response.status_code == 200
        post_ids = [p.id for p in response.context["tweets"]]
        assert post.id in post_ids
        assert other_post.id not in post_ids


@pytest.mark.django_db
class TestLikeToggle:
    def test_like_post(self, client):
        user = UserFactory()
        post = PostFactory()
        client.force_login(user)
        response = client.post(reverse("postknob:like_toggle", kwargs={"pk": post.pk}))
        assert response.status_code == 200
        assert Like.objects.filter(user=user, post=post).exists()

    def test_unlike_post(self, client):
        user = UserFactory()
        post = PostFactory()
        LikeFactory(user=user, post=post)
        client.force_login(user)
        client.post(reverse("postknob:like_toggle", kwargs={"pk": post.pk}))
        assert not Like.objects.filter(user=user, post=post).exists()


@pytest.mark.django_db
class TestBookmark:
    def test_bookmark_post(self, client):
        user = UserFactory()
        post = PostFactory()
        client.force_login(user)
        client.post(reverse("postknob:bookmark_toggle", kwargs={"pk": post.pk}))
        assert Bookmark.objects.filter(user=user, post=post).exists()

    def test_bookmarks_list(self, client):
        user = UserFactory()
        bm = BookmarkFactory(user=user)
        client.force_login(user)
        response = client.get(reverse("postknob:bookmarks"))
        assert response.status_code == 200


@pytest.mark.django_db
class TestComments:
    def test_create_comment(self, client):
        user = UserFactory()
        post = PostFactory()
        client.force_login(user)
        response = client.post(
            reverse("postknob:comment_create", kwargs={"pk": post.pk}),
            {"body": "Great post!"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert Comment.objects.filter(post=post, user=user).exists()


@pytest.mark.django_db
class TestHealthCheck:
    def test_health_check(self, client):
        response = client.get(reverse("health_check"))
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


@pytest.mark.django_db
class TestRegistration:
    def test_register_creates_user(self, client):
        response = client.post(reverse("postknob:register"), {
            "username": "newhobnobber",
            "email": "new@postknob.test",
            "password1": "Str0ng!Pass#99",
            "password2": "Str0ng!Pass#99",
        })
        assert response.status_code == 302
        from django.contrib.auth.models import User
        assert User.objects.filter(username="newhobnobber").exists()
