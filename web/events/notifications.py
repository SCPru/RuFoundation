from renderer import RenderContext, single_pass_render_text

from django.contrib.auth.models import AbstractUser as _UserType

from modules.forumnewpost import OnForumNewPost
from web.views.signup import OnUserSignUp

from django.contrib.auth import get_user_model
from web.models.articles import ArticleLogEntry
from web.controllers.articles import OnEditArticle
from web.models.forum import ForumPost

from web.events import on_trigger
from web.controllers.notifications import get_notification_subscribtions, send_user_notification, UserNotification


User = get_user_model()


@on_trigger(OnUserSignUp)
def signup_notification(e: OnUserSignUp):
    send_user_notification(e.user, UserNotification.NotificationType.Welcome)


@on_trigger(OnForumNewPost)
def new_forum_post_notification(e: OnForumNewPost):
    user: _UserType = e.post.author
    thread = e.post.thread
    thread_name = thread.name if thread.category_id else thread.article.display_name

    # post_preview = single_pass_render_text(e.source, RenderContext(None, None, {}, user), 'message')
    post_preview = e.source
    notification_subscribers = set([subscription.subscriber for subscription in get_notification_subscribtions(forum_thread=e.post.thread)])
    if user in notification_subscribers:
        notification_subscribers.remove(user)

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

        send_user_notification(
            recipients=reply_subscribers,
            type=UserNotification.NotificationType.NewPostReply,
            referred_to=e.url,
            meta={
                'thread_section': thread.category.section.name,
                'thread_category': thread.category.name,
                'thread_name': thread_name,
                'author_name': user.username,
                'origin_title': e.post.reply_to.name,
                'reply_title': e.post.name,
                'reply_preview': post_preview,
                'link': e.url
        })
    
    send_user_notification(
        recipients=notification_subscribers,
        type=UserNotification.NotificationType.NewThreadPost,
        referred_to=e.url,
        meta={
            'thread_section': thread.category.section.name,
            'thread_category': thread.category.name,
            'thread_name': thread_name,
            'author_name': user.username,
            'post_title': e.post.name,
            'post_preview': post_preview,
            'link': e.url
    })


@on_trigger(OnEditArticle)
def new_article_revision_notification(e: OnEditArticle):
    log_entry: ArticleLogEntry = e.log_entry
    notification_subscribers = [subscription.subscriber for subscription in get_notification_subscribtions(article=log_entry.article) if subscription.subscriber != log_entry.user]
    send_user_notification(notification_subscribers, UserNotification.NotificationType.NewArticleRevision, meta={
        'blame': log_entry.user.username,
        'page_name': log_entry.article.full_name,
        'rev_number': log_entry.rev_number,
        'rev_type': log_entry.type,
        'comment': log_entry.comment,
        'referred_to': '/%s' % log_entry.article.full_name
    })