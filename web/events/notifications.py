import logging
import re

from modules.forumnewpost import OnForumNewPost
from modules.forumpost import OnForumEditPost
from renderer.utils import render_user_to_json
from web.controllers import articles
from web.views.signup import OnUserSignUp

from web.models.articles import ArticleLogEntry
from web.controllers.articles import OnEditArticle
from web.models.forum import ForumCategory
from web.models.users import User

from web.events import on_trigger
from web.controllers.notifications import get_notification_subscribtions, send_user_notification, UserNotification


@on_trigger(OnUserSignUp)
def signup_notification(e: OnUserSignUp):
    send_user_notification(e.user, UserNotification.NotificationType.Welcome)


@on_trigger(OnForumNewPost)
def new_forum_post_notification(e: OnForumNewPost):
    user: User = e.post.author

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
            'name': e.title,
            'url': post_url
        },
        'author': render_user_to_json(e.post.author),
        'message_source': e.source
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

        restricted_users = []
        for user in reply_subscribers:
            if not user.has_perm('roles.view_forum_posts', e.post):
                restricted_users.append(user)
        reply_subscribers.difference_update(restricted_users)

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
            meta=reply_meta
        )

    restricted_users = []
    for user in notification_subscribers:
        if not user.has_perm('roles.view_forum_posts', e.post):
            restricted_users.append(user)
    notification_subscribers.difference_update(restricted_users)
    
    send_user_notification(
        recipients=notification_subscribers,
        type=UserNotification.NotificationType.NewThreadPost,
        meta=meta
    )


@on_trigger(OnEditArticle)
def new_article_revision_notification(e: OnEditArticle):
    log_entry: ArticleLogEntry = e.log_entry
    article = log_entry.article
    notification_subscribers = [subscription.subscriber for subscription in get_notification_subscribtions(article=log_entry.article) if subscription.subscriber != log_entry.user and subscription.subscriber.has_perm('roles.view_articles', article)]

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
    })


@on_trigger(OnForumNewPost)
@on_trigger(OnForumEditPost)
def handle_forum_mention(e: OnForumNewPost | OnForumEditPost):
    mention_regex = re.compile(r'(?<=@)[\w.-]+')

    if isinstance(e, OnForumNewPost):
        mentions = set(map(str.lower, re.findall(mention_regex, e.source)))
    else:
        old_mentions = set(map(str.lower, re.findall(mention_regex, e.prev_source)))
        new_mentions = set(map(str.lower, re.findall(mention_regex, e.source)))
        mentions = new_mentions - old_mentions

    mentioned_users = set(User.objects.filter(username__in=mentions, is_active=True).exclude(id=e.user.id))

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
            'name': e.title,
            'url': post_url
        },
        'author': render_user_to_json(e.user),
        'message_source': e.source
    }

    restricted_users = []
    for user in mentioned_users:
        if not user.has_perm('roles.view_forum_posts', e.post):
            restricted_users.append(user)
    mentioned_users -= set(restricted_users)
    
    send_user_notification(
        recipients=mentioned_users,
        type=UserNotification.NotificationType.ForumMention,
        meta=meta
    )