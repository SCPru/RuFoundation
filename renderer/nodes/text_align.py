from .html_base import HTMLBaseNode


class TextAlignNode(HTMLBaseNode):
    @classmethod
    def is_allowed(cls, tag, _parser):
        return tag in ['<', '>', '=', '==']

    def __init__(self, t, _attributes, children):
        super().__init__()
        self.type = t
        self.block_node = True
        for child in children:
            self.append_child(child)

    def render(self, context=None):
        dir = 'left'
        if self.type == '>':
            dir = 'right'
        elif self.type == '=':
            dir = 'center'
        elif self.type == '==':
            dir = 'justify'
        return self.render_template('<div style="text-align: {{align}}">{{content}}</div>', align=dir, content=super().render(context=context))

