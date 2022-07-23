from django.contrib.auth import get_user_model

from .html import HTMLNode
from .html_base import HTMLBaseNode
from ..utils import render_user_to_html
from django.utils import html


User = get_user_model()


class UserNode(HTMLBaseNode):
    is_single_argument = True

    @classmethod
    def is_allowed(cls, tag, _parser):
        return tag in ['user', '*user']

    @classmethod
    def is_single_tag(cls, _tag, _attributes):
        return True

    def __init__(self, tag, attributes, _nothing):
        super().__init__()
        username, _ = HTMLNode.extract_name_from_attributes(attributes)
        avatar = (tag == '*user')
        self.username = username
        self.avatar = avatar

    def render(self, context=None):
        try:
            user = User.objects.get(username=self.username)
            return render_user_to_html(user, avatar=self.avatar)
        except User.DoesNotExist:
            return self.render_template(
                '<span class="error-inline">Пользователь \'{{username}}\' не существует</span>',
                username=self.username
            )

