"""
PostKnob REST API views.

All list/create endpoints use JWT (or session) auth.
Object-level writes (edit/delete) are restricted to the owner.
"""
from __future__ import annotations

from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from postknob.models import Bookmark, Comment, Follow, Like, Post, Profile
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    BookmarkSerializer,
    CommentSerializer,
    FollowSerializer,
    PostSerializer,
    PostWriteSerializer,
    ProfileSerializer,
    UserSerializer,
)


# ---------------------------------------------------------------------------
# Posts
# ---------------------------------------------------------------------------

class PostViewSet(viewsets.ModelViewSet):
    """
    list:   GET  /api/v1/posts/
    create: POST /api/v1/posts/
    retrieve: GET  /api/v1/posts/{id}/
    update: PUT/PATCH /api/v1/posts/{id}/
    destroy: DELETE /api/v1/posts/{id}/
    like:   POST /api/v1/posts/{id}/like/
    unlike: DELETE /api/v1/posts/{id}/like/
    bookmark: POST /api/v1/posts/{id}/bookmark/
    """
    queryset = (
        Post.objects
        .select_related("user", "user__profile")
        .prefetch_related("hashtags", "likes", "comments")
        .order_by("-created_at")
    )
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["text", "hashtags__name", "user__username"]
    ordering_fields = ["created_at", "likes"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return PostWriteSerializer
        return PostSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        _, created = Like.objects.get_or_create(user=request.user, post=post)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response({"liked": True, "like_count": post.likes.count()}, status=status_code)

    @like.mapping.delete
    def unlike(self, request, pk=None):
        post = self.get_object()
        Like.objects.filter(user=request.user, post=post).delete()
        return Response({"liked": False, "like_count": post.likes.count()})

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def bookmark(self, request, pk=None):
        post = self.get_object()
        _, created = Bookmark.objects.get_or_create(user=request.user, post=post)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response({"bookmarked": True}, status=status_code)

    @bookmark.mapping.delete
    def unbookmark(self, request, pk=None):
        post = self.get_object()
        Bookmark.objects.filter(user=request.user, post=post).delete()
        return Response({"bookmarked": False})


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        post_id = self.kwargs.get("post_pk")
        return (
            Comment.objects
            .filter(post_id=post_id)
            .select_related("user", "user__profile")
            .order_by("created_at")
        )

    def perform_create(self, serializer):
        post = generics.get_object_or_404(Post, pk=self.kwargs["post_pk"])
        serializer.save(user=self.request.user, post=post)


# ---------------------------------------------------------------------------
# Feed
# ---------------------------------------------------------------------------

class FeedView(generics.ListAPIView):
    """Personalised feed: posts from followed users, newest first."""
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ["-created_at"]

    def get_queryset(self):
        following_ids = self.request.user.following.values_list("following_id", flat=True)
        return (
            Post.objects
            .filter(user_id__in=following_ids)
            .select_related("user", "user__profile")
            .prefetch_related("hashtags", "likes", "comments")
            .order_by("-created_at")
        )


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """GET / PATCH own profile or view others' profiles."""
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "user__username"
    lookup_url_kwarg = "username"
    queryset = Profile.objects.select_related("user")

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]


class UserListView(generics.ListAPIView):
    """Search / list users."""
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "email"]
    queryset = User.objects.select_related("profile").all()


class UserDetailView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "username"
    queryset = User.objects.select_related("profile")


# ---------------------------------------------------------------------------
# Follow
# ---------------------------------------------------------------------------

class FollowView(APIView):
    """
    POST   /api/v1/users/{username}/follow/  → follow
    DELETE /api/v1/users/{username}/follow/  → unfollow
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, username):
        target = generics.get_object_or_404(User, username=username)
        if target == request.user:
            return Response({"detail": "Cannot follow yourself."}, status=400)
        _, created = Follow.objects.get_or_create(follower=request.user, following=target)
        return Response(
            {"following": True, "follower_count": target.followers.count()},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request, username):
        target = generics.get_object_or_404(User, username=username)
        Follow.objects.filter(follower=request.user, following=target).delete()
        return Response({"following": False, "follower_count": target.followers.count()})


class FollowersListView(generics.ListAPIView):
    serializer_class = FollowSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user = generics.get_object_or_404(User, username=self.kwargs["username"])
        return Follow.objects.filter(following=user).select_related("follower", "following")


class FollowingListView(generics.ListAPIView):
    serializer_class = FollowSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user = generics.get_object_or_404(User, username=self.kwargs["username"])
        return Follow.objects.filter(follower=user).select_related("follower", "following")


# ---------------------------------------------------------------------------
# Bookmarks
# ---------------------------------------------------------------------------

class BookmarkListView(generics.ListAPIView):
    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Bookmark.objects
            .filter(user=self.request.user)
            .select_related("post", "post__user", "post__user__profile")
            .order_by("-created_at")
        )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({"status": "ok", "version": "1.0"})
