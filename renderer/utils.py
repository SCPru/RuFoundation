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
    if user.type == User.UserType.Wikidot:
        return 'wd:'+user.wikidot_username
    return user.username


def render_user_to_html(user: User, avatar=True, hover=True):
    if user is None:
        return render_template_from_string(
            '<span class="printuser{{class_add}}"><strong>system</strong></span>',
             class_add=(' avatarhover' if hover else '')
        )
    if isinstance(user, AnonymousUser):
        return render_template_from_string(
            """
            <span class="printuser{{class_add}}">
                {% if show_avatar %}
                    <a onclick="return false;"><img class="small" src="{{avatar}}" alt="Anonymous User"></a>
                {% endif %}
                <a onclick="return false;">Anonymous User</a>
            </span>
            """,
            class_add=(' avatarhover' if hover else ''),
            show_avatar=avatar,
            avatar=settings.ANON_AVATAR
        )
    if user.type == 'wikidot':
        user_avatar = settings.WIKIDOT_AVATAR
        username = user.wikidot_username
    else:
        user_avatar = user.get_avatar(default=settings.DEFAULT_AVATAR)
        username = user.username
    return render_template_from_string(
        """
        <span class="printuser w-user{{class_add}}" data-user-id="{{user_id}}" data-user-name="{{username}}">
            {% if show_avatar %}
                <a href="/-/users/{{user_id}}-{{username}}"><img class="small" src="{{avatar}}" alt="{{username}}"></a>
            {% endif %}
            <a href="/-/users/{{user_id}}-{{username}}">{{username}}</a>
        </span>
        """,
        class_add=(' avatarhover' if hover else ''),
        show_avatar=avatar,
        avatar=user_avatar,
        user_id=user.id,
        username=username
    )


def render_user_to_json(user: User, avatar=True):
    if user is None:
        return {'type': 'system'}
    if isinstance(user, AnonymousUser):
        return {'type': 'anonymous', 'avatar': None, 'name': 'Anonymous User', 'username': None, 'showAvatar': avatar}
    user_type = 'user'
    if user.type != User.UserType.Normal:
        user_type = user.type
    username = user.username
    if user.type == User.UserType.Wikidot:
        username = user.wikidot_username
    return {'type': user_type, 'id': user.id, 'avatar': user.get_avatar(), 'name': username, 'username': username, 'showAvatar': avatar}
