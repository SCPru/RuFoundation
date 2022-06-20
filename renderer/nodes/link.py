from . import Node
from django.utils import html


class LinkNode(Node):
    def __init__(self, url, text, blank=False, exists=True):
        super().__init__()
        self.url = LinkNode.filter_url(url)
        self.text = text
        self.blank = blank
        self.exists = exists

    @staticmethod
    def filter_url(url):
        url = url.strip()
        if url.startswith('javascript:'):
            return '#'
        return url

    def render(self, context=None):
        blank = ' target="_blank"' if self.blank else ''
        cls = ' class="newpage"' if not self.exists else ''
        return '<a href="%s"%s%s>%s</a>' % (html.escape(self.url), blank, cls, html.escape(self.text))
