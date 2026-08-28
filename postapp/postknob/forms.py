from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Comment, Post, Profile


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["text", "photo"]
        widgets = {
            "text": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "What's on your mind, hobnobber?",
                "class": "w-full bg-zinc-800 text-white border border-zinc-700 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-yellow-400 resize-none",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["photo"].widget.attrs.update({"class": "block text-sm text-zinc-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-yellow-400 file:text-black hover:file:bg-yellow-300"})


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field_class = "w-full bg-zinc-800 text-white border border-zinc-700 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-yellow-400"
        for field in self.fields.values():
            field.widget.attrs.update({"class": field_class})


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["bio", "avatar", "website", "location"]
        widgets = {
            "bio": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Tell the world about yourself…",
                "class": "w-full bg-zinc-800 text-white border border-zinc-700 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-yellow-400 resize-none",
            }),
            "website": forms.URLInput(attrs={
                "placeholder": "https://yoursite.com",
                "class": "w-full bg-zinc-800 text-white border border-zinc-700 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-yellow-400",
            }),
            "location": forms.TextInput(attrs={
                "placeholder": "City, Country",
                "class": "w-full bg-zinc-800 text-white border border-zinc-700 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-yellow-400",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["avatar"].widget.attrs.update({"class": "block text-sm text-zinc-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-yellow-400 file:text-black hover:file:bg-yellow-300"})


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {
            "body": forms.TextInput(attrs={
                "placeholder": "Add a comment…",
                "class": "flex-1 bg-zinc-800 text-white border border-zinc-700 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-yellow-400 text-sm",
            }),
        }
        labels = {"body": ""}
