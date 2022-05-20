import ResizeObserver from "resize-observer-polyfill";

export function makeAutoResizeFrame(node: HTMLElement) {

    // hack: mark node as already processed because it was
    if ((node as any)._autoresize) {
        return
    }
    (node as any)._autoresize = true;
    // end hack

    const frame: HTMLIFrameElement = node as HTMLIFrameElement;

    const setFrameHeight = () => {
        const body = frame.contentDocument.body;
        const html = frame.contentDocument.documentElement;
        const height = Math.max( body.scrollHeight, body.offsetHeight,
            html.clientHeight, html.scrollHeight, html.offsetHeight );
        frame.style.minHeight = `${height}px`;
    };

    frame.addEventListener('load', () => {
       setFrameHeight();
       const observer = new ResizeObserver(() => {
           setFrameHeight();
       });
       observer.observe(frame.contentDocument.body);
    });

}