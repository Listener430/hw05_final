from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User

POST_NUMBER = 10
NUMB = 30


def index(request):
    posts = Post.objects.all().select_related("author")
    paginator = Paginator(posts, POST_NUMBER)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
    }
    return render(request, "posts/index.html", context)


def group_posts(request, slug):

    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all().select_related("author")
    paginator = Paginator(posts, POST_NUMBER)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "group": group,
        "page_obj": page_obj,
    }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    following = False
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, POST_NUMBER)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    count = posts.count()
    if request.user.is_authenticated:
        user = get_object_or_404(User, username=request.user)
        if Follow.objects.filter(user=user, author=author).exists():
            following = True
    context = {
        "page_obj": page_obj,
        "author": author,
        "count": count,
        "following": following,
    }
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    # post = get_object_or_404(Post, id=post_id)
    post = Post.objects.filter(id=post_id).first()
    count = post.author.posts.all().count()
    first_ch = post.text[0:NUMB]
    comments = post.comments.all()
    context = {
        "post": post,
        "count": count,
        "first_ch": first_ch,
        "comments": comments,
        "form": CommentForm(),
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST, files=request.FILES or None)
        user = get_object_or_404(User, username=request.user)
        if form.is_valid():
            deform = form.save(commit=False)
            deform.author = user
            deform.save()
            return redirect(f"/profile/{user.username}/")
        return render(request, "posts/create_post.html", {"form": form})

    form = PostForm()
    return render(request, "posts/create_post.html", {"form": form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != get_object_or_404(User, username=request.user):
        return redirect(f"/posts/{post_id}")
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
        initial={"group": post.group, "text": post.text},
    )
    is_edit = True
    author = get_object_or_404(User, username=request.user)
    if form.is_valid():
        deform = form.save(commit=False)
        deform.author = author
        deform.save()
        return redirect(f"/posts/{post_id}/")
    context = {
        "post": post,
        "form": form,
        "is_edit": is_edit,
    }
    return render(request, "posts/create_post.html", context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect("posts:post_detail", post_id=post_id)
    form = CommentForm()

    context = {
        "post": post,
        "form": form,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def follow_index(request):
    user = get_object_or_404(User, username=request.user)
    authors = user.follower.values("author")
    posts = Post.objects.filter(author__in=authors)
    paginator = Paginator(posts, POST_NUMBER)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
    }
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=request.user)
    author = get_object_or_404(User, username=username)
    if author != user:
        if Follow.objects.filter(author=author, user=user).count() == 0:
            Follow.objects.create(author=author, user=user)
            authors = user.follower.values("author")
            posts = Post.objects.filter(author__in=authors)
            paginator = Paginator(posts, POST_NUMBER)
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)
            context = {
                "page_obj": page_obj,
                "author": author,
            }
            return render(request, "posts/follow.html", context)
    return redirect(f"/profile/{user.username}/")


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=request.user)
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(author=author, user=user).delete()
    authors = user.follower.values("author")
    posts = Post.objects.filter(author__in=authors)
    paginator = Paginator(posts, POST_NUMBER)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
    }
    return render(request, "posts/follow.html", context)