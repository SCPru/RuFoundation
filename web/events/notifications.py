from django.contrib.auth.models import AbstractUser as _UserType

from modules.forumnewpost import OnForumNewPost
from renderer.utils import render_user_to_json
from web.controllers import articles
from web.views.signup import OnUserSignUp

from django.contrib.auth import get_user_model
from web.models.articles import ArticleLogEntry
from web.controllers.articles import OnEditArticle
from web.models.forum import ForumCategory, ForumPostVersion

from web.events import on_trigger
from web.controllers.notifications import get_notification_subscribtions, send_user_notification, UserNotification


User = get_user_model()


@on_trigger(OnUserSignUp)
def signup_notification(e: OnUserSignUp):
    send_user_notification(e.user, UserNotification.NotificationType.Welcome)


@on_trigger(OnForumNewPost)
def new_forum_post_notification(e: OnForumNewPost):
    user: _UserType = e.post.author

    latest_version = ForumPostVersion.objects.filter(post=e.post).order_by('-created_at')[:1]
    message_source = latest_version[0].source if latest_version else ''

    notification_subscribers = set([subscription.subscriber for subscription in get_notification_subscribtions(forum_thread=e.post.thread)])
    if user in notification_subscribers:
        notification_subscribers.remove(user)

    thread = e.post.thread
    category = thread.category
    if not category:
        # find first category that matches
        for c in ForumCategory.objects.filter(is_for_comments=True):
            category = c
            break
    section = category.section

    thread_name = thread.name if thread.category_id else thread.article.display_name

    section_url = '/forum/s-%d/%s' % (section.id, articles.normalize_article_name(section.name)) if category else ''
    category_url = '/forum/c-%d/%s' % (category.id, articles.normalize_article_name(category.name)) if category else ''
    thread_url = '/forum/t-%d/%s' % (thread.id, articles.normalize_article_name(thread_name))
    post_url = '%s#post-%d' % (thread_url, e.post.id)

    meta = {
        'thread': {
            'id': thread.id,
            'name': thread_name,
            'url': thread_url
        },
        'category': {
            'id': category.id,
            'name': category.name,
            'url': category_url
        },
        'section': {
            'id': section.id,
            'name': section.name,
            'url': section_url
        },
        'post': {
            'id': e.post.id,
            'name': e.post.name,
            'url': post_url
        },
        'author': render_user_to_json(e.post.author),
        'message_source': message_source
    }

    if e.post.reply_to:
        reply_subscribers = []
        curr_post = e.post
        for _ in range(UserNotification.POST_REPLY_TTL):
            reply_subscribers.append(curr_post.author)
            curr_post = curr_post.reply_to
            if not curr_post:
                break

        reply_subscribers = set(reply_subscribers)
        if user in reply_subscribers:
            reply_subscribers.remove(user)
        notification_subscribers -= reply_subscribers

        origin_post_url = '%s#post-%d' % (thread_url, e.post.reply_to.id)

        reply_meta = dict(meta)
        reply_meta['origin'] = {
            'id': e.post.reply_to.id,
            'name': e.post.reply_to.name,
            'url': origin_post_url
        }

        send_user_notification(
            recipients=reply_subscribers,
            type=UserNotification.NotificationType.NewPostReply,
            referred_to=post_url,
            meta=reply_meta
        )
    
    send_user_notification(
        recipients=notification_subscribers,
        type=UserNotification.NotificationType.NewThreadPost,
        referred_to=post_url,
        meta=meta
    )


@on_trigger(OnEditArticle)
def new_article_revision_notification(e: OnEditArticle):
    log_entry: ArticleLogEntry = e.log_entry
    notification_subscribers = [subscription.subscriber for subscription in get_notification_subscribtions(article=log_entry.article) if subscription.subscriber != log_entry.user]

    article = log_entry.article

    send_user_notification(notification_subscribers, UserNotification.NotificationType.NewArticleRevision, meta={
        'user': render_user_to_json(log_entry.user),
        'article': {
            'uid': article.id,
            'pageId': article.full_name,
            'title': article.title,
        },
        'rev_id': log_entry.id,
        'rev_meta': log_entry.meta,
        'rev_number': log_entry.rev_number,
        'rev_type': log_entry.type,
        'comment': log_entry.comment
    }, referred_to='/%s' % log_entry.article.full_name)
