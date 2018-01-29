from django.shortcuts import render, get_object_or_404, HttpResponseRedirect
from .models import Post, Comment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import EmailPostForm, CommentForm
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from taggit.models import Tag
from django.db.models import Count
# Create your views here.

def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False

    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # send mail here
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = '{} ({}) recommends you reading "{}"'.format(cd['name'], cd['email'], post.title)
            message = 'Read "{}" at {}\n\n{}\'s comments: {}'.format(post.title, post_url, cd['name'], cd['comments'])
            send_mail(subject, message, 'admin@myblog.com',[cd['to']])
            sent = True
    else:
        form = EmailPostForm()

    context = {
        'form': form,
        'post': post,
        'sent': sent,
    }

    return render(request, 'blog/post/share.html', context)


def post_list(request, tag_slug=None):

    object_list = Post.published.all()
    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])

    paginator = Paginator(object_list, 2) # 2 post in each page
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    context = {
        'posts': posts,
        'page': page,
        'tag': tag,
    }

    return render(request, 'blog/post/list.html', context)


def post_detail(request, year, month, day, post ):
    post = get_object_or_404(Post, status='published', slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)

    # list of active comments for this post
    comments = post.comments.filter(active=True)
    new_comment_created = False
    if request.method == 'POST':
        # comment is posted
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # create comment object not to save in db yet
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.save()
            new_comment_created = True
            return HttpResponseRedirect(post.get_absolute_url())
    else:
        comment_form = CommentForm()

    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.objects.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(
        same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]

    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'new_comment_created': new_comment_created,
        'similar_posts': similar_posts,
    }

    return render(request, 'blog/post/detail.html', context)