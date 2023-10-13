import json
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from operator import itemgetter

from .models import User, Post


def index(request):
    # Gets posts and sets up paginator
    posts = Post.objects.all().order_by('-timestamp')
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Renders page with paginator information
    return render(request, "network/index.html", {
        "posts": posts,
        "page_obj": page_obj,
        "page_number": range(1, paginator.num_pages+1)
    })

@login_required
def post(request):
    if request.method == "POST":
        # Creates a new post object from submitted form and redirects to index
        body = request.POST['body']
        Post.objects.create(poster=request.user, body=body)
        return HttpResponseRedirect(reverse("index"))

def user(request, id):
    # Gets a specific user's posts
    poster = User.objects.get(id=id)
    poster_posts = poster.posts.all().order_by('-timestamp')

    # Sets up paginator into 10 pages (see docs)
    paginator = Paginator(poster_posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Renders page with paginator information
    return render(request, "network/profile.html", {
        "poster": poster,
        "page_obj": page_obj,
        "page_number": range(1, paginator.num_pages+1)
    })

def following(request):
    user_following = request.user.following.all()
    following_posts = []

    # Makes list of all the followed users' posts (probably not an efficient way to do this)
    for user_followed in user_following:
        posts = user_followed.posts.all()
        for post in posts:
            following_posts.append(post)

    # Sorts followed posts by timestamp
    following_posts = sorted(following_posts, key=lambda post : post.timestamp, reverse=True)
    # Sets up paginator into 10 pages (see Django paginator docs)
    paginator = Paginator(following_posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    print(paginator.num_pages)

    # Renders page with paginator information
    return render(request, "network/following.html", {
        "posts": following_posts,
        "page_obj": page_obj,
        "page_number": range(1, paginator.num_pages+1)
    })

@login_required
def follow_unfollow(request, poster_id):
    # Checks request
    if request.method == "POST":
        # Gets button which could can have one of two values
        button = request.POST["following_btn"]

        current_user = User.objects.get(id=request.user.id)
        poster = User.objects.get(id=poster_id)

        # Checks type of button, either follows or unfollows, respectively
        if button == "Follow":
            print(button)
            current_user.following.add(poster)
            poster.followers.add(current_user)
            print(reverse("user", kwargs={"id": poster_id}))
            return HttpResponseRedirect(reverse("user", kwargs={"id": poster_id}))
        else:
            current_user.following.remove(poster)
            poster.followers.remove(current_user)
            return HttpResponseRedirect(reverse("user", kwargs={"id": poster_id}))

@csrf_exempt
@login_required
def edit(request, post_id):
    # Queries for post, exception just in case
    try:
        post = Post.objects.get(post_id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found."}, status=404)

    # Checks if user is attempting to edit their own post, sends error response otherwise
    if post.poster.id != request.user.id:
        return JsonResponse({"error": "You cannot edit this post."}, status=403)

    # Allows two option for dealing with posts, GET to request and PUT to edit
    if request.method == "GET":
        return JsonResponse(post.serialize())
    elif request.method == "PUT":
        # Grabs JSON data from request
        data = json.loads(request.body)

        # Checks if text is present and updates post object
        if data.get("text") is not None:
            post.body = data["text"]
            post.save()

        # Returns 204 meaning success but don't refresh
        return HttpResponse(status=204)
    else:
        return JsonResponse({
            "error": "GET or PUT request required."
        }, status=400)

@csrf_exempt
@login_required
def like(request, post_id):
    # Queries for post, exception just in case
    try:
        post = Post.objects.get(post_id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found."}, status=404)

    # Makes sure user can't like their own post
    if post.poster.id == request.user.id:
        return JsonResponse({"error": "You cannot like this post."}, status=403)

    # If user has previously liked, removes like. Otherwise, addds like
    if post in request.user.liked_posts.all():
        post.likers.remove(request.user)
        return JsonResponse(post.serialize())
    else:
        post.likers.add(request.user)
        return JsonResponse(post.serialize())

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")
