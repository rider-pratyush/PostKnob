from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission: only the owner of an object can edit/delete it.
    Read access is allowed to any request (authenticated or not).
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # obj.user covers Post, Comment, Like, Bookmark
        owner = getattr(obj, "user", None) or getattr(obj, "follower", None)
        return owner == request.user


class IsAuthenticatedOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """Re-export for convenience."""
    pass
