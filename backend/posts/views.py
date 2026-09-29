from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Post, Like, Comment


def feed(request):
    posts = Post.objects.all().order_by("-created_at")

    return render(request, "posts/feed.html", {
        "posts": posts
    })


@login_required
def create_post(request):

    if request.method == "POST":

        image = request.FILES.get("image")
        caption = request.POST.get("caption", "").strip()

        if image:
            Post.objects.create(
                author=request.user,
                image=image,
                caption=caption
            )

        return redirect("feed")

    return render(request, "posts/create_post.html")


@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    like = Like.objects.filter(
        user=request.user,
        post=post
    ).first()

    if like:
        like.delete()
    else:
        Like.objects.create(
            user=request.user,
            post=post
        )

    return redirect("feed")


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == "POST":
        text = request.POST.get("comment", "").strip()

        if text:
            Comment.objects.create(
                user=request.user,
                post=post,
                text=text
            )

    return redirect("feed")

@login_required
def profile(request):
    user_posts = Post.objects.filter(
        author=request.user
    ).order_by("-created_at")

    return render(request, "posts/profile.html", {
        "profile_user": request.user,
        "user_posts": user_posts,
    })