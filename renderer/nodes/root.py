from . import Node
from web import threadvars


class RootNode(Node):
    def render(self, context=None):
        with threadvars.context():
            threadvars.put('render_context', context)
            threadvars.put('render_globals', dict())
            super().pre_render(context=context)
            return super().render(context=context)
