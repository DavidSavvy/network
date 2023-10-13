from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("post", views.post, name="post"),
    path("user/<str:id>", views.user, name="user"),
    path("follow_unfollow/<str:poster_id>", views.follow_unfollow, name="follow_unfollow"),
    path("following", views.following, name="following"),

    # API Paths
    path("edit/<str:post_id>", views.edit, name="edit"),
    path("like/<str:post_id>", views.like, name="like")
]
