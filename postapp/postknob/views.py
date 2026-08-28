"""
PostKnob views — social-media CRUD, profiles, follow/like/comment/bookmark,
feed, search, hashtags, and health-check.
"""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CommentForm, PostForm, ProfileEditForm, UserRegistrationForm
from .models import Bookmark, Comment, Follow, Hashtag, Like, Post, Profile
from .tasks import process_post_image

User = get_user_model()

# ---------------------------------------------------------------------------
# Landing / Home
# ---------------------------------------------------------------------------

def index(request):
    return redirect("home")


def home(request):
    trending_posts = Post.objects.select_related("user", "user__profile").order_by("-created_at")[:6]
    hobnobbers = User.objects.select_related("profile").all()[:8]
    return render(request, "home.html", {
        "trending_posts": trending_posts,
        "hobnobbers": hobnobbers,
    })


def about(request):
    return render(request, "about.html")


def health_check(request):
    """Simple health-check endpoint for load-balancers / uptime monitors."""
    return JsonResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# Posts
# ---------------------------------------------------------------------------

def tweet_list(request):
    """Public explore page — all posts, newest first, paginated."""
    q = request.GET.get("q", "").strip()
    qs = Post.objects.select_related("user", "user__profile").prefetch_related("hashtags", "likes")
    if q:
        qs = qs.filter(Q(text__icontains=q) | Q(hashtags__name__icontains=q)).distinct()
    qs = qs.order_by("-created_at")
    paginator = Paginator(qs, 12)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "tweet_list.html", {"tweets": page, "q": q})


def tweet_detail(request, pk):
    tweet = get_object_or_404(
        Post.objects.select_related("user", "user__profile").prefetch_related("hashtags", "likes"),
        pk=pk,
    )
    comments = tweet.comments.select_related("user", "user__profile").order_by("created_at")
    comment_form = CommentForm()
    liked = request.user.is_authenticated and tweet.likes.filter(user=request.user).exists()
    bookmarked = request.user.is_authenticated and tweet.bookmarks.filter(user=request.user).exists()
    return render(request, "tweet_detail.html", {
        "tweet": tweet,
        "comments": comments,
        "comment_form": comment_form,
        "liked": liked,
        "bookmarked": bookmarked,
    })


@login_required
def tweet_create(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            form.save_m2m()  # saves hashtags
            
            if post.photo:
                process_post_image.delay(post.pk)
                
            messages.success(request, "Post created! 🎉")
            return redirect("postknob:tweet_detail", pk=post.pk)
    else:
        form = PostForm()
    return render(request, "tweet_form.html", {"form": form, "action": "Create"})


@login_required
def tweet_edit(request, tweet_id):
    tweet = get_object_or_404(Post, pk=tweet_id, user=request.user)
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=tweet)
        if form.is_valid():
            form.save()
            if tweet.photo:
                process_post_image.delay(tweet.pk)
            messages.success(request, "Post updated!")
            return redirect("postknob:tweet_detail", pk=tweet.pk)
    else:
        form = PostForm(instance=tweet)
    return render(request, "tweet_form.html", {"form": form, "action": "Edit"})


@login_required
def tweet_delete(request, tweet_id):
    tweet = get_object_or_404(Post, pk=tweet_id, user=request.user)
    if request.method == "POST":
        tweet.delete()
        messages.success(request, "Post deleted.")
        return redirect("postknob:tweet_list")
    return render(request, "tweet_confirm_delete.html", {"tweet": tweet})


# ---------------------------------------------------------------------------
# Feed
# ---------------------------------------------------------------------------

@login_required
def feed_view(request):
    """Personalised feed using Fan-Out on Write Redis cache."""
    from .services import get_feed_post_ids, FEED_LIMIT
    
    # Get up to FEED_LIMIT post IDs from Redis (very fast)
    post_ids = get_feed_post_ids(request.user.id, 0, FEED_LIMIT)
    
    # Paginate the IDs first to avoid fetching all 500 objects from DB
    paginator = Paginator(post_ids, 10)
    page = paginator.get_page(request.GET.get("page"))
    
    # Fetch only the posts for the current page
    if page.object_list:
        posts = (
            Post.objects.filter(id__in=page.object_list)
            .select_related("user", "user__profile")
            .prefetch_related("hashtags", "likes")
        )
        # Preserve Redis ordering (newest first)
        posts_dict = {p.id: p for p in posts}
        sorted_posts = [posts_dict[pid] for pid in page.object_list if pid in posts_dict]
        page.object_list = sorted_posts
        
    return render(request, "feed.html", {"tweets": page})


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    posts = (
        Post.objects.filter(user=profile_user)
        .select_related("user", "user__profile")
        .prefetch_related("hashtags", "likes")
        .order_by("-created_at")
    )
    paginator = Paginator(posts, 9)
    page = paginator.get_page(request.GET.get("page"))
    is_following = (
        request.user.is_authenticated
        and Follow.objects.filter(follower=request.user, following=profile_user).exists()
    )
    follower_count = profile_user.followers.count()
    following_count = profile_user.following.count()
    return render(request, "profile.html", {
        "profile_user": profile_user,
        "posts": page,
        "is_following": is_following,
        "follower_count": follower_count,
        "following_count": following_count,
    })


def followers_list(request, username):
    profile_user = get_object_or_404(User, username=username)
    # The users who follow this user
    followers = User.objects.filter(following__following=profile_user).select_related("profile")
    paginator = Paginator(followers, 20)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "user_list.html", {
        "profile_user": profile_user, 
        "users": page,
        "title": "Followers",
        "empty_msg": "No followers yet."
    })

def following_list(request, username):
    profile_user = get_object_or_404(User, username=username)
    # The users this user follows
    following = User.objects.filter(followers__follower=profile_user).select_related("profile")
    paginator = Paginator(following, 20)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "user_list.html", {
        "profile_user": profile_user, 
        "users": page,
        "title": "Following",
        "empty_msg": "Not following anyone yet."
    })


@login_required
def profile_edit(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated!")
            return redirect("postknob:profile", username=request.user.username)
    else:
        form = ProfileEditForm(instance=profile)
    return render(request, "profile_edit.html", {"form": form})


# ---------------------------------------------------------------------------
# Follow (HTMX-friendly)
# ---------------------------------------------------------------------------

@login_required
@require_POST
def follow_toggle(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return HttpResponse("You can't follow yourself.", status=400)
    follow, created = Follow.objects.get_or_create(follower=request.user, following=target)
    if not created:
        follow.delete()
        is_following = False
        from .tasks import process_unfollow_feed
        process_unfollow_feed.delay(request.user.id, target.id)
    else:
        is_following = True
        from .tasks import process_follow_feed
        process_follow_feed.delay(request.user.id, target.id)
    follower_count = target.followers.count()
    # HTMX partial response
    return render(request, "partials/follow_btn.html", {
        "profile_user": target,
        "is_following": is_following,
        "follower_count": follower_count,
    })


# ---------------------------------------------------------------------------
# Likes (HTMX-friendly)
# ---------------------------------------------------------------------------

@login_required
@require_POST
def like_toggle(request, pk):
    post = get_object_or_404(Post, pk=pk)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    like_count = post.likes.count()
    return render(request, "partials/like_btn.html", {
        "tweet": post,
        "liked": liked,
        "like_count": like_count,
    })


# ---------------------------------------------------------------------------
# Bookmarks (HTMX-friendly)
# ---------------------------------------------------------------------------

@login_required
@require_POST
def bookmark_toggle(request, pk):
    post = get_object_or_404(Post, pk=pk)
    bm, created = Bookmark.objects.get_or_create(user=request.user, post=post)
    if not created:
        bm.delete()
        bookmarked = False
    else:
        bookmarked = True
    return render(request, "partials/bookmark_btn.html", {
        "tweet": post,
        "bookmarked": bookmarked,
    })


@login_required
def bookmarks_list(request):
    bms = (
        Bookmark.objects.filter(user=request.user)
        .select_related("post", "post__user", "post__user__profile")
        .order_by("-created_at")
    )
    paginator = Paginator(bms, 12)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "bookmarks.html", {"bookmarks": page})


# ---------------------------------------------------------------------------
# Comments (HTMX-friendly)
# ---------------------------------------------------------------------------

@login_required
@require_POST
def comment_create(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.post = post
        comment.save()
    comments = post.comments.select_related("user", "user__profile").order_by("created_at")
    return render(request, "partials/comment_section.html", {
        "tweet": post,
        "comments": comments,
        "comment_form": CommentForm(),
    })


@login_required
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk, user=request.user)
    post_pk = comment.post_id
    comment.delete()
    if request.headers.get("HX-Request"):
        post = get_object_or_404(Post, pk=post_pk)
        comments = post.comments.select_related("user", "user__profile").order_by("created_at")
        return render(request, "partials/comment_section.html", {
            "tweet": post,
            "comments": comments,
            "comment_form": CommentForm(),
        })
    return redirect("postknob:tweet_detail", pk=post_pk)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search_view(request):
    q = request.GET.get("q", "").strip()
    posts = []
    if q:
        posts = (
            Post.objects.filter(Q(text__icontains=q) | Q(hashtags__name__icontains=q))
            .distinct()
            .select_related("user", "user__profile")
            .prefetch_related("hashtags", "likes")
            .order_by("-created_at")
        )
        paginator = Paginator(posts, 12)
        posts = paginator.get_page(request.GET.get("page"))
    return render(request, "search.html", {"posts": posts, "q": q})


# ---------------------------------------------------------------------------
# Hashtags
# ---------------------------------------------------------------------------

def hashtag_view(request, slug):
    hashtag = get_object_or_404(Hashtag, slug=slug)
    posts = (
        Post.objects.filter(hashtags=hashtag)
        .select_related("user", "user__profile")
        .prefetch_related("hashtags", "likes")
        .order_by("-created_at")
    )
    paginator = Paginator(posts, 12)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "hashtag.html", {"hashtag": hashtag, "posts": page})


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to PostKnob, {user.username}! 🎉")
            return redirect("postknob:tweet_list")
    else:
        form = UserRegistrationForm()
    return render(request, "registration/register.html", {"form": form})


def logout_view(request):
    auth_logout(request)
    messages.success(request, "See ya, hobnobber! 👋")
    return redirect("home")
