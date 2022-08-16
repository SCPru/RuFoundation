from web.models.sites import get_current_site
from .html import HTMLNode
from .html_base import HTMLBaseNode
from web.controllers import articles
from django.conf import settings


class ImageNode(HTMLBaseNode):
    @classmethod
    def is_allowed(cls, tag, _parser):
        return tag in ['image', '=image', '>image', '<image', 'f<image', 'f>image']

    @classmethod
    def is_single_tag(cls, _tag, _attributes):
        return True

    def __init__(self, img_type, attributes, _nothing):
        super().__init__()
        source, attributes = HTMLNode.extract_name_from_attributes(attributes)
        self.img_type = img_type
        self.source = source
        self.attributes = attributes

    def get_image_url(self, context=None):
        if context is None or context.source_article is None:
            return None
        src_lower = self.source.lower()
        if src_lower.startswith('/'):
            path = '%s%s' % (settings.MEDIA_URL, src_lower.lstrip('/'))
        else:
            if '/' in src_lower:
                return self.source
            path = '%s%s/%s' % (settings.MEDIA_URL, articles.get_full_name(context.source_article), self.source)
        media_host = get_current_site().media_domain
        path = '//' + media_host + path
        return path

    def render(self, context=None):
        url = self.get_image_url(context)
        attributes = HTMLNode.set_attribute(self.attributes, 'class', HTMLNode.get_attribute(self.attributes, 'class', '')+' image')
        attr_string = HTMLNode.render_attributes(attributes, ['style', 'class', 'width', 'height'])
        # image_tags = ['image', '=image', '>image', '<image', 'f<image', 'f>image']

        return self.render_template(
            ''.join([
                "{% if type == 'image' %}",
                '<img src="{{src}}" alt="{{alt}}" {{attrs}}>',
                "{% elif type == 'f<image' %}",
                '<div class="image-container floatleft">',
                    '<img src="{{src}}" alt="{{alt}}" {{attrs}}>',
                '</div>',
                "{% elif type == 'f>image' %}",
                '<div class="image-container floatright">',
                    '<img src="{{src}}" alt="{{alt}}" {{attrs}}>',
                '</div>',
                "{% elif type == '=image' %}",
                '<div style="display: flex; justify-content: center">',
                    '<img src="{{src}}" alt="{{alt}}" {{attrs}}>',
                '</div>',
                "{% elif type == '<image' %}",
                '<div style="display: flex; justify-content: flex-start">',
                    '<img src="{{src}}" alt="{{alt}}" {{attrs}}>',
                '</div>',
                "{% elif type == '>image' %}",
                '<div style="display: flex; justify-content: flex-end">',
                    '<img src="{{src}}" alt="{{alt}}" {{attrs}}>',
                '</div>',
                '{% endif %}'
            ]),
            type=self.img_type,
            src=url,
            alt=self.source.replace('\\', '/').split('/')[-1],
            attrs=attr_string
        )
