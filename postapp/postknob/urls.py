from django.urls import path

from . import views

app_name = "postknob"

urlpatterns = [
    # --- Posts ---
    path("", views.tweet_list, name="tweet_list"),
    path("create/", views.tweet_create, name="tweet_create"),
    path("post/<int:pk>/", views.tweet_detail, name="tweet_detail"),
    path("<int:tweet_id>/edit/", views.tweet_edit, name="tweet_edit"),
    path("<int:tweet_id>/delete/", views.tweet_delete, name="tweet_delete"),

    # --- Feed ---
    path("feed/", views.feed_view, name="feed"),

    # --- Interactions (HTMX) ---
    path("post/<int:pk>/like/", views.like_toggle, name="like_toggle"),
    path("post/<int:pk>/bookmark/", views.bookmark_toggle, name="bookmark_toggle"),
    path("post/<int:pk>/comment/", views.comment_create, name="comment_create"),
    path("comment/<int:pk>/delete/", views.comment_delete, name="comment_delete"),

    # --- Bookmarks ---
    path("bookmarks/", views.bookmarks_list, name="bookmarks"),

    # --- Search ---
    path("search/", views.search_view, name="search"),

    # --- Hashtags ---
    path("hashtag/<slug:slug>/", views.hashtag_view, name="hashtag"),

    # --- Profiles ---
    path("profile/<str:username>/", views.profile_view, name="profile"),
    path("profile/<str:username>/followers/", views.followers_list, name="followers_list"),
    path("profile/<str:username>/following/", views.following_list, name="following_list"),
    path("profile/<str:username>/follow/", views.follow_toggle, name="follow_toggle"),
    path("settings/profile/", views.profile_edit, name="profile_edit"),

    # --- Auth ---
    path("register/", views.register, name="register"),
    path("logout/", views.logout_view, name="logout"),

    # --- Static ---
    path("about/", views.about, name="about"),
]
