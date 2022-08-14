from . import Node


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
        test_url = url.lower()
        if test_url.startswith('javascript:') or test_url.startswith('data:'):
            return '#invalid-url'
        return url

    def render(self, context=None):
        return self.render_template(
            '<a href="{{url}}"{% if blank %}target="_blank"{% endif %}{% if not exists %} class="newpage"{% endif %}>{{text}}</a>',
            blank=self.blank,
            exists=self.exists,
            text=self.text,
            url=self.url
        )

    def plain_text(self, context=None):
        return self.text
