from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.shortcuts import resolve_url
import urllib.parse
from django.utils import html


User = get_user_model()


def render_user_to_text(user: User):
    if user is None:
        return 'system'
    if isinstance(user, AnonymousUser):
        return 'Anonymous User'
    return user.username


def render_user_to_html(user: User, avatar=True):
    if user is None:
        return '<span class="printuser"><strong>system</strong></span>'
    if isinstance(user, AnonymousUser):
        ret = '<span class="printuser">'
        if avatar:
            ret += '<a onclick="return false;"><img class="small" src="/static/images/anon_avatar.png" alt="Anonymous User"></a>'
        ret += '<a onclick="return false;">Anonymous User</a>'
        ret += '</span>'
        return ret
    ret = '<span class="printuser w-user" data-user-name="%s">' % html.escape(user.username)
    if avatar:
        ret += '<a href="/-/users/%d-%s"><img class="small" src="%s" alt="%s"></a>' % (user.id, urllib.parse.quote_plus(user.username), user.avatar, html.escape(user.username))
    ret += '<a href="/-/users/%d-%s">%s</a>' % (user.id, urllib.parse.quote_plus(user.username), html.escape(user.username))
    ret += '</span>'
    return ret


def render_user_to_json(user: User, avatar=True):
    if user is None:
        return {'type': 'system'}
    if isinstance(user, AnonymousUser):
        return {'type': 'anonymous', 'avatar': '/static/images/anon_avatar.png', 'name': 'Anonymous User', 'username': None, 'showAvatar': avatar}
    return {'type': 'user', 'id': user.id, 'avatar': resolve_url("local_files", user.avatar), 'name': user.username, 'username': user.username, 'showAvatar': avatar}