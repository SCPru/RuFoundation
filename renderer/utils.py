from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from django.template import Context, Template
from django.utils import html

from system.models import User

import threading
import urllib.parse


_templates = dict()
_templates_lock = threading.RLock()


def render_template_from_string(template: str, **context):
    with _templates_lock:
        if template in _templates:
            tpl = _templates[template]
        else:
            tpl = _templates[template] = Template(template.strip())
    return tpl.render(Context(context))


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
            ret += '<a onclick="return false;"><img class="small" src="%s" alt="Anonymous User"></a>' % settings.ANNON_AVATAR
        ret += '<a onclick="return false;">Anonymous User</a>'
        ret += '</span>'
        return ret
    ret = '<span class="printuser w-user" data-user-name="%s">' % html.escape(user.username)
    if avatar:
        ret += '<a href="/-/users/%d-%s"><img class="small" src="%s" alt="%s"></a>' % (user.id, urllib.parse.quote_plus(user.username), user.get_avatar(), html.escape(user.username))
    ret += '<a href="/-/users/%d-%s">%s</a>' % (user.id, urllib.parse.quote_plus(user.username), html.escape(user.username))
    ret += '</span>'
    return ret


def render_user_to_json(user: User, avatar=True):
    if user is None:
        return {'type': 'system'}
    if isinstance(user, AnonymousUser):
        return {'type': 'anonymous', 'avatar': settings.ANNON_AVATAR, 'name': 'Anonymous User', 'username': None, 'showAvatar': avatar}
    return {'type': 'user', 'id': user.id, 'avatar': user.get_avatar(), 'name': user.username, 'username': user.username, 'showAvatar': avatar}