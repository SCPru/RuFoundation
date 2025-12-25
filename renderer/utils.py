import threading
import urllib.parse

from enum import Enum
from typing import Literal, Optional, Union

from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from django.template import Context, Template
from django.utils.safestring import SafeString

from web.models.articles import Vote
from web.models.roles import Role, RoleBadgeJSON, RoleIconJSON
from web.models.settings import Settings
from web.models.site import get_current_site
from web.models.users import User
from web.controllers import articles
from web.util.pydantic import JSONInterface
from web.types import _UserType


_templates = dict()
_templates_lock = threading.RLock()


def render_template_from_string(template: str, **context: object) -> SafeString:
    with _templates_lock:
        if template in _templates:
            tpl = _templates[template]
        else:
            tpl = _templates[template] = Template(template.strip())
    return tpl.render(Context(context))


class RoleJSON(JSONInterface):
    slug: str
    name: Optional[str]=None
    shortName: Optional[str]=None
    category: Optional[int]=None
    staff: bool=False
    groupVotes: bool=False
    inlineVisualMode: Union[Role.InlineVisualMode, str]=Role.InlineVisualMode.Hidden
    profileVisualMode: Union[Role.ProfileVisualMode, str]=Role.ProfileVisualMode.Hidden
    icon: Optional[RoleIconJSON]=None
    badge: Optional[RoleBadgeJSON]=None


def render_role_to_json(role: Role):
    if role is None:
        return RoleJSON()
    
    tail = role.get_name_tail()
    return RoleJSON(
        slug=role.slug,
        name=role.name,
        shortName=role.short_name,
        category=role.category.id if role.category else None,
        staff=role.is_staff,
        groupVotes=role.group_votes,
        inlineVisualMode=role.inline_visual_mode,
        profileVisualMode=role.profile_visual_mode,
        icon=tail if isinstance(tail, RoleIconJSON) else None,
        badge=tail if isinstance(tail, RoleBadgeJSON) else None
    )


def render_user_to_text(user: _UserType):
    if user is None:
        return 'system'
    if isinstance(user, AnonymousUser):
        return 'Anonymous User'
    if user.type == User.UserType.Wikidot:
        return 'wd:'+user.wikidot_username
    return user.username


def render_user_to_html(user: _UserType, avatar=True, hover=True):
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

    return render_template_from_string(
        """
        <span class="printuser w-user{{class_add}}" data-user-id="{{user_id}}" data-user-name="{{username}}">
            {% if show_avatar %}
                <a href="/-/users/{{user_id}}-{{username}}"><img class="small" src="{{avatar}}" alt="{{displayname}}"></a>
            {% endif %}
            <a href="/-/users/{{user_id}}-{{username}}">{{displayname}}</a>
            {% if show_avatar %}
                {% for icon in tails.icons %}
                    <span class="icon" {% if icon.tooltip %}title="{{icon.tooltip|safe}}"{% endif %}><img src="data:image/svg+xml,{{icon.icon}}"/></span>
                {% endfor %}
                {% for badge in tails.badges %}
                    <span class="badge" {% if badge.tooltip %}title="{{badge.tooltip|safe}}"{% endif %} style="background: {{badge.bg|safe}}; color: {{badge.text_color|safe}}; {% if badge.show_border %}border: solid 1px {{badge.text_color|safe}}{% endif %}">{{badge.text|safe}}</span>
                {% endfor %}
            {% endif %}
        </span>
        """,
        class_add=(' avatarhover' if hover else ''),
        show_avatar=avatar,
        tails=user.name_tails,
        avatar=user_avatar,
        user_id=user.pk,
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


class APIUserType(Enum):
    Anonymous='anonymous'
    Normal='normal'
    Wikidot='wikidot'
    System='system'
    Bot='bot'


class UserJSON(JSONInterface):
    type: Union[User.UserType, Literal['anonymous'], str]='anonymous'
    id: Optional[int]=None
    name: Optional[str]=None
    username: Optional[str]=None
    isActive: bool=True
    avatar: Optional[str]=None
    showAvatar: bool=False
    admin: bool=False
    staff: bool=False
    editor: Optional[bool]=False
    roles: Optional[list[str]]=None


def render_user_to_json(user: _UserType, show_avatar=True, skip_perms=False):
    if user is None:
        return UserJSON(type=User.UserType.System)
    if isinstance(user, AnonymousUser):
        return UserJSON(
            type='anonymous',
            name='Anonymous User',
            username=None,
            showAvatar=show_avatar
        )
    return UserJSON(
        type=user.type,
        id=user.pk,
        name=user.__str__(),
        username=user.username,
        isActive=user.is_active,
        avatar=user.get_avatar(),
        showAvatar=show_avatar,
        admin=user.is_superuser,
        staff=user.is_staff,
        editor=user.has_perm('roles.edit_articles') if not skip_perms else None,
        roles=[role.slug for role in user.roles.all() if role.is_visual]
    )

def render_vote_to_html(vote: Vote, mode=Settings.RatingMode.Default, capitalize=True):
    if mode == Settings.RatingMode.Disabled:
        return ''

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

    if mode == Settings.RatingMode.Default:
        mode = Settings.get_default_settings().rating_mode

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


def get_resource(uri, context, full_url=False):
    uri = filter_url(uri)
    prefix = ''

    if full_url:
        domain = get_current_site().media_domain
        prefix = f'https://{domain}'

    if not uri:
        return None
    if '//' in uri:
        return uri
    else:
        uri = uri.removeprefix('/')
        if '/' in uri:
            return f'{prefix}/local--files/{uri}'
        else:
            return f'{prefix}/local--files/{context.article.full_name}/{uri}'