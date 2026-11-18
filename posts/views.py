"""
Posts and replies (ST-I4, ST-P7, ST-S4, SF-I4, SF-P7, SF-S4).

  /posts/               read the posts and publish a new one
  /posts/<id>/reply/    reply to a post

For Students and Staff, instead of class WhatsApp groups. Every view starts with the
same two checks: logged in, and the right role (explained at the top of core/views.py).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Role

from .forms import PostForm
from .models import Post


@login_required
def post_list(request):
    """Shows the posts, newest first, 10 on a page, each with its replies. The form at the top publishes a post."""
    if request.user.role not in (Role.STUDENT, Role.STAFF):
        raise PermissionDenied

    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            Post.objects.create(user=request.user, text=form.cleaned_data['text'])      # ST-S4 / SF-S4
            messages.success(request, 'Your post is published.')
            return redirect('posts:list')
    else:
        form = PostForm()

    # Only new posts here (reply_to is empty). Their replies are fetched with them.
    posts = Post.objects.filter(reply_to=None).select_related('user').prefetch_related('replies__user')
    page = Paginator(posts, 10).get_page(request.GET.get('page'))
    return render(request, 'posts/post_list.html', {'form': form, 'page': page})


@login_required
def reply(request, post_id):
    """Reply to a post. Replies go one level deep: a reply cannot be replied to."""
    if request.user.role not in (Role.STUDENT, Role.STAFF):
        raise PermissionDenied

    post = get_object_or_404(Post, pk=post_id, reply_to=None)
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            Post.objects.create(user=request.user, reply_to=post, text=form.cleaned_data['text'])
            messages.success(request, 'Your reply is published.')
        else:
            messages.error(request, 'Write something before replying (up to 280 characters).')
    return redirect('posts:list')
