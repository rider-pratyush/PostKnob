from django.shortcuts import render
from .models import Post
from .forms import PostForm, UserRegistrationForm
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, get_user_model
import requests
from anime_api.apis import NekosAPI

nekos = NekosAPI()


# Create your views here.
def index(request):
    return render(request, 'index.html')

def home(request):
    trending_posts = Post.objects.all().order_by('-created_at')[:4]
    User = get_user_model()
    hobnobbers = User.objects.all()[:8]
    return render(request, 'home.html', {
        'trending_posts': trending_posts,
        'hobnobbers': hobnobbers,
    })

from django.contrib.auth.models import User
from django.db import models

# class Profile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png')

#     def __str__(self):
#         return self.user.username


def tweet_list(request):
    tweets = Post.objects.all().order_by('-created_at')
    return render(request, 'tweet_list.html', {'tweets': tweets})

@login_required
def tweet_create(request):
    if request.method == 'POST':
      form = PostForm(request.POST, request.FILES)
      if form.is_valid():
        tweet=  form.save(commit=False)
        tweet.user = request.user
        tweet.save()
        return redirect('tweet_list')
    else:
        form = PostForm()
    return render(request, 'tweet_form.html', {'form':form})

@login_required
def tweet_edit(request, tweet_id):
   tweet = get_object_or_404(Post, pk= tweet_id, user = request.user) 
   if request.method == 'POST':
    form = PostForm(request.POST, request.FILES, instance = tweet)
    if form.is_valid():
       tweet = form.save(commit=False)
       tweet.user = request.user
       tweet.save()
       return redirect('tweet_list')
   else:
     form = PostForm(instance=tweet)
   return render(request, 'tweet_form.html', {'form':form})

@login_required
def tweet_delete(request, tweet_id):
   tweet = get_object_or_404(Post, pk = tweet_id, user = request.user)
   if request.method == 'POST':
      tweet.delete()
      return redirect('tweet_list')
   return render(request, 'tweet_confirm_delete.html', {'tweet':tweet})

# def register(request):
#    if request.method =='POST':
#       form = UserRegistrationForm(request.POST)
#       if form.is_valid():
#          user = form.save(commit=False)
#          user.set_password(form.cleaned_data['password1'])
#          user.save()
#          login(request, user)
#          return redirect('tweet_list')
#    else:
#       form = UserRegistrationForm()
#    return render(request, 'registration/register.html', {'form': form})

from anime_api.apis import nekos_api
from django.conf import settings

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Assign avatar
            try:
                nekos = nekos_api.NekosAPI()
                img_obj = nekos.get_random_image()
                avatar_url = img_obj.url if img_obj else "https://i.imgur.com/1Q9Z1Zm.png"
            except Exception as e:
                print("Error fetching avatar:", e)
                avatar_url = "https://i.imgur.com/1Q9Z1Zm.png"
            # Create user profile with avatar_url
            user.profile.avatar_url = avatar_url
            user.profile.save()
            login(request, user)
            return redirect('tweet_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect

def logout_view(request):
    auth_logout(request)
    messages.success(request, "See ya, hobnobber! 👋")
    return redirect('home')

def about(request):
    return render(request, 'about.html')

def tweet_detail(request, pk):
   tweet=get_object_or_404(Post, pk=pk)
   return render(request, 'tweet_detail.html', {'tweet':tweet})
