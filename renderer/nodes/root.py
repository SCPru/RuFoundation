from . import Node
from web import threadvars


class RootNode(Node):
    def render(self, context=None):
        with threadvars.context():
            threadvars.put('render_context', context)
            return super().render(context=context)
