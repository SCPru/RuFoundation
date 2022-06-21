from .html_base import HTMLBaseNode
from django.utils import html
import uuid


class UnsafeHTMLNode(HTMLBaseNode):
    is_raw_text = True

    @classmethod
    def is_allowed(cls, tag, _parser):
        return tag == 'html'

    def __init__(self, _tag, _attributes, code):
        super().__init__()
        self.code = code
        self.block_node = True

    def render(self, context=None):
        frame_id = str(uuid.uuid4())
        resize_code = """
        <script>
        (function(){
            let lastHeight = 0;
            function doFrame() {
                const body = document.body;
                const html = document.documentElement;
                const height = Math.max(body && body.scrollHeight, body && body.offsetHeight,
                    html.clientHeight, html.scrollHeight, html.offsetHeight, body && body.getBoundingClientRect().height);
                window.requestAnimationFrame(doFrame);
                if (lastHeight !== height) {
                    parent.postMessage({type: 'iframe-change-height', payload: { height, id: '%s' }}, '*');
                    lastHeight = height;
                }
            }
            doFrame();
        })();
        </script>
        """ % frame_id
        code = resize_code + self.code
        return '<iframe id="%s" srcdoc="%s" sandbox="allow-scripts allow-top-navigation allow-popups" style="width: 100%%; height: 0" class="w-iframe-autoresize" frameborder="0" allowtransparency="true"></iframe>' % (frame_id, html.escape(code))
