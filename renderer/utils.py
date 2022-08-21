from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from django.template import Context, Template

from system.models import User

import threading


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
        displayname = 'wd:'+user.wikidot_username
    else:
        user_avatar = user.get_avatar(default=settings.DEFAULT_AVATAR)
        displayname = user.username
    return render_template_from_string(
        """
        <span class="printuser w-user{{class_add}}" data-user-id="{{user_id}}" data-user-name="{{username}}">
            {% if show_avatar %}
                <a href="/-/users/{{user_id}}-{{username}}"><img class="small" src="{{avatar}}" alt="{{displayname}}"></a>
            {% endif %}
            <a href="/-/users/{{user_id}}-{{username}}">{{displayname}}</a>
        </span>
        """,
        class_add=(' avatarhover' if hover else ''),
        show_avatar=avatar,
        avatar=user_avatar,
        user_id=user.id,
        username=user.username,
        displayname=displayname
    )


def render_user_to_json(user: User, avatar=True):
    if user is None:
        return {'type': 'system'}
    if isinstance(user, AnonymousUser):
        return {'type': 'anonymous', 'avatar': None, 'name': 'Anonymous User', 'username': None, 'showAvatar': avatar}
    user_type = 'user'
    if user.type != User.UserType.Normal:
        user_type = user.type
    displayname = user.username
    if user.type == User.UserType.Wikidot:
        displayname = 'wd:'+user.wikidot_username
    staff = user.is_staff
    admin = user.is_superuser
    return {'type': user_type, 'id': user.id, 'avatar': user.get_avatar(), 'name': displayname, 'username': user.username, 'showAvatar': avatar, 'staff': staff, 'admin': admin}


def filter_url(url):
    url = url.strip()
    test_url = url.lower()
    if test_url.startswith('javascript:') or test_url.startswith('data:'):
        return '#invalid-url'
    return url
