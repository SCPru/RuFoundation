from .html import HTMLNode
from .html_base import HTMLBaseNode
from web.controllers import articles
from django.conf import settings
from django.utils import html


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
        self.complex_node = True

    def _get_image_url(self, context=None):
        if context is None or context.source_article is None:
            return None
        src_lower = self.source.lower()
        if '/' in src_lower:
            return self.source
        path = '%s%s/%s' % (settings.MEDIA_URL, articles.get_full_name(context.source_article), self.source)
        if settings.MEDIA_HOST is not None:
            path = '//' + settings.MEDIA_HOST + path
        return path

    def render(self, context=None):
        url = self._get_image_url(context)
        attributes = HTMLNode.set_attribute(self.attributes, 'class', HTMLNode.get_attribute(self.attributes, 'class', '')+' image')
        attr_string = HTMLNode.render_attributes(attributes, ['style', 'class', 'width', 'height'])
        # image_tags = ['image', '=image', '>image', '<image', 'f<image', 'f>image']
        if self.img_type == 'image':
            return '<img src="%s" alt="%s" %s>' %\
                   (html.escape(url), html.escape(self.source), attr_string)
        elif self.img_type in ['f>image', 'f<image']:
            outer_cls = 'floatleft' if self.img_type == 'f<image' else 'floatright'
            return '<div class="image-container %s"><img src="%s" alt="%s" %s></div>' % (outer_cls, html.escape(url), html.escape(self.source), attr_string)
        elif self.img_type == '=image':
            return '<div style="display: flex; justify-content: center"><img src="%s" alt="%s" %s></div>' %\
                   (html.escape(url), html.escape(self.source), attr_string)
        elif self.img_type == '<image':
            return '<div style="display: flex; justify-content: flex-start"><img src="%s" alt="%s" %s></div>' %\
                   (html.escape(url), html.escape(self.source), attr_string)
        elif self.img_type == '>image':
            return '<div style="display: flex; justify-content: flex-end"><img src="%s" alt="%s" %s></div>' %\
                   (html.escape(url), html.escape(self.source), attr_string)
        return ''
