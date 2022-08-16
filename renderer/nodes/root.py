from . import Node
from web import threadvars


class RootNode(Node):
    def render(self, context=None):
        with threadvars.context():
            threadvars.put('render_context', context)
            threadvars.put('render_globals', dict())
            super().pre_render(context=context)
            return super().render(context=context)

    def plain_text(self, context=None):
        with threadvars.context():
            threadvars.put('render_context', context)
            threadvars.put('render_globals', dict())
            super().pre_render(context=context)
            return super().plain_text(context=context)

    def render_with_plain_text(self, context=None):
        with threadvars.context():
            threadvars.put('render_context', context)
            threadvars.put('render_globals', dict())
            super().pre_render(context=context)
            r = super().render(context=context)
            t = super().plain_text(context=context)
            return r, t
