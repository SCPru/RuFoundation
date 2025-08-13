import json


def get_html_injected_code(html_id: str) -> str:
    return """
    <script>
    (function(){
        let lastHeight = 0;
        function doFrame() {
            const body = document.body;
            const html = document.documentElement;
            const height = Math.max(body && body.scrollHeight, body && body.offsetHeight, html.offsetHeight, body && body.getBoundingClientRect().height, html.scrollHeight);
            window.requestAnimationFrame(doFrame);
            if (lastHeight !== height) {
                parent.postMessage({type: 'iframe-change-height', payload: { height, id: %s } }, '*');
                lastHeight = height;
            }
        }
        doFrame();
    })();
    const apiHandler = {
        get(target, name) {
            return (async (...args) => {
                const data = {
                    type: "ApiCall",
                    target: name,
                    callId: Math.random(),
                    args
                }
                window.parent.postMessage(data, "*");
                let result;
                const responsePromise = new Promise((resolve) => {
                    const listener = (e) => {
                        if (!e.data.hasOwnProperty("type") || 
                            !e.data.hasOwnProperty("target") || 
                            !e.data.hasOwnProperty("callId") || 
                            !e.data.hasOwnProperty("response") || 
                            e.data.type !== "ApiResponse" ||
                            e.data.callId !== data.callId)
                            return;
                        window.removeEventListener("message", listener);
                        result = e.data.response;
                        resolve();
                    }
                    window.addEventListener("message", listener);
                });
                await responsePromise;
                return result;
            });
        }
    }
    const api = new Proxy({}, apiHandler);
    </script>
    <style>
      body { margin: 0; }
    </style> 
    """ % json.dumps(html_id)
