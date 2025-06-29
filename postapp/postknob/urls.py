# from django.contrib import admin
# from django.urls import path
# from django.conf import settings
# from django.conf.urls.static import static
from django.urls import path
from . import views
from .views import logout_view
urlpatterns = [
    path('', views.tweet_list, name='tweet_list'),
    path('create/', views.tweet_create, name='tweet_create'),
    path('<int:tweet_id>/edit/', views.tweet_edit, name='tweet_edit'),
    path('<int:tweet_id>/delete/', views.tweet_delete, name='tweet_delete'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('about/', views.about, name='about'),
    path('post/<int:pk>/',views.tweet_detail, name='tweet_detail'),
] 
