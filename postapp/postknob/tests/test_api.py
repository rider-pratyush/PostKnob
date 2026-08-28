"""
API tests: JWT auth, CRUD, follow, like, bookmark, feed, pagination, error cases.
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from postknob.models import Follow, Like, Bookmark, Post
from .factories import BookmarkFactory, FollowFactory, LikeFactory, PostFactory, UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client():
    """Returns (client, user) with JWT authentication."""
    user = UserFactory()
    client = APIClient()
    # Obtain JWT token
    response = client.post("/api/token/", {"username": user.username, "password": "testpass123"})
    token = response.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client, user


@pytest.mark.django_db
class TestHealthAPI:
    def test_health_endpoint(self, api_client):
        response = api_client.get("/api/v1/health/")
        assert response.status_code == 200
        assert response.data["status"] == "ok"


@pytest.mark.django_db
class TestJWTAuth:
    def test_obtain_token(self, api_client):
        user = UserFactory()
        response = api_client.post("/api/token/", {"username": user.username, "password": "testpass123"})
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_wrong_credentials(self, api_client):
        response = api_client.post("/api/token/", {"username": "nobody", "password": "wrong"})
        assert response.status_code == 401


@pytest.mark.django_db
class TestPostsAPI:
    def test_list_posts_public(self, api_client):
        PostFactory.create_batch(5)
        response = api_client.get("/api/v1/posts/")
        assert response.status_code == 200
        assert response.data["count"] == 5

    def test_create_post_authenticated(self, auth_client):
        client, user = auth_client
        response = client.post("/api/v1/posts/", {"text": "API test post"})
        assert response.status_code == 201
        assert Post.objects.filter(text="API test post", user=user).exists()

    def test_create_post_unauthenticated(self, api_client):
        response = api_client.post("/api/v1/posts/", {"text": "Should fail"})
        assert response.status_code == 401

    def test_delete_own_post(self, auth_client):
        client, user = auth_client
        post = PostFactory(user=user)
        response = client.delete(f"/api/v1/posts/{post.pk}/")
        assert response.status_code == 204
        assert not Post.objects.filter(pk=post.pk).exists()

    def test_delete_other_post_forbidden(self, auth_client):
        client, user = auth_client
        other_post = PostFactory()
        response = client.delete(f"/api/v1/posts/{other_post.pk}/")
        assert response.status_code == 403

    def test_search_posts(self, api_client):
        PostFactory(text="django rest framework")
        PostFactory(text="python celery")
        response = api_client.get("/api/v1/posts/?search=django")
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_pagination(self, api_client):
        PostFactory.create_batch(25)
        response = api_client.get("/api/v1/posts/")
        assert "next" in response.data
        assert len(response.data["results"]) == 20  # default PAGE_SIZE


@pytest.mark.django_db
class TestLikeAPI:
    def test_like_post(self, auth_client):
        client, user = auth_client
        post = PostFactory()
        response = client.post(f"/api/v1/posts/{post.pk}/like/")
        assert response.status_code == 201
        assert Like.objects.filter(user=user, post=post).exists()

    def test_unlike_post(self, auth_client):
        client, user = auth_client
        post = PostFactory()
        LikeFactory(user=user, post=post)
        response = client.delete(f"/api/v1/posts/{post.pk}/like/")
        assert response.status_code == 200
        assert not Like.objects.filter(user=user, post=post).exists()


@pytest.mark.django_db
class TestFollowAPI:
    def test_follow_user(self, auth_client):
        client, user = auth_client
        target = UserFactory()
        response = client.post(f"/api/v1/users/{target.username}/follow/")
        assert response.status_code == 201
        assert Follow.objects.filter(follower=user, following=target).exists()

    def test_unfollow_user(self, auth_client):
        client, user = auth_client
        target = UserFactory()
        FollowFactory(follower=user, following=target)
        response = client.delete(f"/api/v1/users/{target.username}/follow/")
        assert response.status_code == 200
        assert not Follow.objects.filter(follower=user, following=target).exists()

    def test_cannot_follow_self(self, auth_client):
        client, user = auth_client
        response = client.post(f"/api/v1/users/{user.username}/follow/")
        assert response.status_code == 400


@pytest.mark.django_db
class TestFeedAPI:
    def test_feed_requires_auth(self, api_client):
        response = api_client.get("/api/v1/feed/")
        assert response.status_code == 401

    def test_feed_returns_followed_posts(self, auth_client):
        client, user = auth_client
        followed = UserFactory()
        FollowFactory(follower=user, following=followed)
        post = PostFactory(user=followed)
        other = PostFactory()
        response = client.get("/api/v1/feed/")
        assert response.status_code == 200
        ids = [p["id"] for p in response.data["results"]]
        assert post.pk in ids
        assert other.pk not in ids


@pytest.mark.django_db
class TestBookmarkAPI:
    def test_bookmark_and_list(self, auth_client):
        client, user = auth_client
        post = PostFactory()
        client.post(f"/api/v1/posts/{post.pk}/bookmark/")
        response = client.get("/api/v1/bookmarks/")
        assert response.status_code == 200
        assert response.data["count"] == 1


@pytest.mark.django_db
class TestUsersAPI:
    def test_list_users(self, api_client):
        UserFactory.create_batch(3)
        response = api_client.get("/api/v1/users/")
        assert response.status_code == 200

    def test_user_detail(self, api_client):
        user = UserFactory()
        response = api_client.get(f"/api/v1/users/{user.username}/")
        assert response.status_code == 200
        assert response.data["username"] == user.username

    def test_user_not_found(self, api_client):
        response = api_client.get("/api/v1/users/nonexistent/")
        assert response.status_code == 404
