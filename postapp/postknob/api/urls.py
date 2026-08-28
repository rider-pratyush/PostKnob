from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BookmarkListView,
    CommentViewSet,
    FeedView,
    FollowersListView,
    FollowingListView,
    FollowView,
    HealthCheckView,
    PostViewSet,
    ProfileDetailView,
    UserDetailView,
    UserListView,
)

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post")
# Flat comment endpoint: /api/v1/posts/{post_pk}/comments/
# Using SimpleRouter sub-inclusion approach (no extra package needed)

urlpatterns = [
    # Router-based
    path("", include(router.urls)),

    # Nested-style comments via explicit path
    path("posts/<int:post_pk>/comments/", CommentViewSet.as_view({"get": "list", "post": "create"}), name="post-comments-list"),
    path("posts/<int:post_pk>/comments/<int:pk>/", CommentViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="post-comments-detail"),

    # Feed
    path("feed/", FeedView.as_view(), name="api-feed"),

    # Users
    path("users/", UserListView.as_view(), name="api-users"),
    path("users/<str:username>/", UserDetailView.as_view(), name="api-user-detail"),
    path("users/<str:username>/follow/", FollowView.as_view(), name="api-follow"),
    path("users/<str:username>/followers/", FollowersListView.as_view(), name="api-followers"),
    path("users/<str:username>/following/", FollowingListView.as_view(), name="api-following"),
    path("users/<str:username>/profile/", ProfileDetailView.as_view(), name="api-profile"),

    # Bookmarks
    path("bookmarks/", BookmarkListView.as_view(), name="api-bookmarks"),

    # Health
    path("health/", HealthCheckView.as_view(), name="api-health"),

    # DRF browsable auth
    path("auth/", include("rest_framework.urls")),
]

