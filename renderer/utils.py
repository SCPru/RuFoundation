from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from django.template import Context, Template

from web.models.articles import Vote
from web.models.settings import Settings
from web.models.users import User
from web.controllers import articles

import threading
import urllib.parse


_templates = dict()
_templates_lock = threading.RLock()


def render_template_from_string(template: str, **context: object) -> object:
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
                <a onclick="return false;">Anonymous User</a></span>
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
    
    badge = user.get_badge()

    return render_template_from_string(
        """
        <span class="printuser w-user{{class_add}}" data-user-id="{{user_id}}" data-user-name="{{username}}">
            {% if show_avatar %}
                <a href="/-/users/{{user_id}}-{{username}}"><img class="small" src="{{avatar}}" alt="{{displayname}}"></a>
            {% endif %}
            <a href="/-/users/{{user_id}}-{{username}}">{{displayname}}</a>
            {% if show_avatar and badge.show %}
                <span class="badge" style="background: {{badge.bg}}; color: {{badge.text_color}}; {% if badge.border %}outline: solid 1px {{badge.text_color}}{% endif %}">{{badge.text}}</span>
            {% endif %}
        </span>
        """,
        class_add=(' avatarhover' if hover else ''),
        show_avatar=avatar,
        badge=badge,
        avatar=user_avatar,
        user_id=user.id,
        username=user.username,
        displayname=displayname
    )


def render_external_user_to_html(username: str, avatar=True, hover=True):
    displayname = username
    username = articles.normalize_article_name(username)
    return render_template_from_string(
        """
        <span class="printuser w-user{{class_add}}" data-user-id="{{user_id}}" data-user-name="{{username}}">
            {% if show_avatar %}
                <a href="https://www.wikidot.com/user:info/{{username}}" target="_blank"><img class="small" src="{{avatar}}" alt="{{displayname}}"></a>
            {% endif %}
            <a href="https://www.wikidot.com/user:info/{{username}}" target="_blank">{{displayname}}</a></span>
        """,
        class_add=(' avatarhover' if hover else ''),
        show_avatar=avatar,
        avatar=settings.WIKIDOT_AVATAR,
        user_id=-1,
        username=username,
        displayname=displayname
    )


def render_user_to_json(user: User, avatar=True):
    if user is None:
        return {'type': 'system'}
    if isinstance(user, AnonymousUser):
        return {
            'type': 'anonymous',
            'avatar': None,
            'name': 'Anonymous User',
            'username': None,
            'showAvatar': avatar
        }
    user_type = 'user'
    if user.type != User.UserType.Normal:
        user_type = user.type
    displayname = user.username
    if user.type == User.UserType.Wikidot:
        displayname = 'wd:'+user.wikidot_username
    staff = user.is_staff
    admin = user.is_superuser
    editor = user.is_editor
    return {
        'type': user_type,
        'id': user.id,
        'avatar': user.get_avatar(),
        'name': displayname,
        'username': user.username,
        'showAvatar': avatar,
        'staff': staff,
        'admin': admin,
        'editor': editor,
        'visualGroup': user.visual_group.name if user.visual_group else None,
        'visualGroupIndex': user.visual_group.index if user.visual_group else None
    }

def render_vote_to_html(vote: Vote, mode=Settings.RatingMode.Stars, capitalize=True):
    rate = vote.rate if vote else None

    if vote is None:
        msg = 'не оценено'
        if capitalize:
            msg = msg.capitalize()
        return render_template_from_string(
            """
            <span class="vote" title="Оценка обсуждаемой статьи">{{msg}}</span>
            """,
            msg=msg
        )

    if mode == Settings.RatingMode.UpDown:
        visual_rate = '%+d' % rate
    elif mode == Settings.RatingMode.Stars:
        visual_rate = '%.1f' % rate
    else:
        visual_rate = '%d' % rate

    return render_template_from_string(
        """
        <span class="vote" title="Оценка обсуждаемой статьи"><span class="rate">{{visual_rate}}</span>
        """,
        visual_rate=visual_rate
    )

def validate_url(url):
    url = url.strip()
    try:
        r = urllib.parse.urlparse(url)
        if r.scheme.lower() in ['javascript', 'data']:
            raise ValueError(repr(url))
    except:
        raise ValueError(repr(url))
    return url


def filter_url(url):
    try:
        return validate_url(url)
    except ValueError:
        return '#invalid-url'


def get_boolean_param(params: dict, key, default=False):
    value = params.get(key, default)
    if isinstance(value, str):
        value = value.lower()
    if value in ['true', 't', '1', 'yes']:
        return True
    if value in ['false', 'f', '0', 'no']:
        return False
    return default
