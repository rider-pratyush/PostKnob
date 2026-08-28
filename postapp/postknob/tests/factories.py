"""
Factory Boy factories for all PostKnob models.
"""
import factory
from django.contrib.auth.models import User

from postknob.models import Bookmark, Comment, Follow, Hashtag, Like, Post, Profile


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@postknob.test")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")


class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profile

    user = factory.SubFactory(UserFactory)
    bio = factory.Faker("sentence")
    location = factory.Faker("city")
    website = factory.Faker("url")


class HashtagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Hashtag

    name = factory.Sequence(lambda n: f"tag{n}")


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    user = factory.SubFactory(UserFactory)
    text = factory.Faker("paragraph")

    @factory.post_generation
    def hashtags(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tag in extracted:
                self.hashtags.add(tag)


class FollowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Follow

    follower = factory.SubFactory(UserFactory)
    following = factory.SubFactory(UserFactory)


class LikeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Like

    user = factory.SubFactory(UserFactory)
    post = factory.SubFactory(PostFactory)


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    user = factory.SubFactory(UserFactory)
    post = factory.SubFactory(PostFactory)
    body = factory.Faker("sentence")


class BookmarkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Bookmark

    user = factory.SubFactory(UserFactory)
    post = factory.SubFactory(PostFactory)
