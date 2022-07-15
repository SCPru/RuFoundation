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


def render_user_to_html(user: User, avatar=True, hover=True):
    if user is None:
        return '<span class="printuser%s"><strong>system</strong></span>' % (' avatarhover' if hover else '')
    if isinstance(user, AnonymousUser):
        ret = '<span class="printuser%s">' % (' avatarhover' if hover else '')
        if avatar:
            ret += '<a onclick="return false;"><img class="small" src="%s" alt="Anonymous User"></a>' % settings.ANON_AVATAR
        ret += '<a onclick="return false;">Anonymous User</a>'
        ret += '</span>'
        return ret
    ret = '<span class="printuser w-user%s" data-user-name="%s">' % ((' avatarhover' if hover else ''), html.escape(user.username))
    if avatar:
        ret += '<a href="/-/users/%d-%s"><img class="small" src="%s" alt="%s"></a>' % (user.id, urllib.parse.quote_plus(user.username), user.get_avatar(default=settings.DEFAULT_AVATAR), html.escape(user.username))
    ret += '<a href="/-/users/%d-%s">%s</a>' % (user.id, urllib.parse.quote_plus(user.username), html.escape(user.username))
    ret += '</span>'
    return ret


def render_user_to_json(user: User, avatar=True):
    if user is None:
        return {'type': 'system'}
    if isinstance(user, AnonymousUser):
        return {'type': 'anonymous', 'avatar': None, 'name': 'Anonymous User', 'username': None, 'showAvatar': avatar}
    user_type = 'user'
    if user.type != User.UserType.Normal:
        user_type = user.type
    return {'type': user_type, 'id': user.id, 'avatar': user.get_avatar(), 'name': user.username, 'username': user.username, 'showAvatar': avatar}
