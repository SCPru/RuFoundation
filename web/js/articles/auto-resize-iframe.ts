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
        try {
            const body = frame.contentDocument.body;
            const html = frame.contentDocument.documentElement;
            const height = Math.max(body.scrollHeight, body.offsetHeight,
                html.clientHeight, html.scrollHeight, html.offsetHeight, body.getBoundingClientRect().height);
            const heightProp = `${height}px`;
            if (frame.style.minHeight !== heightProp) {
                frame.style.minHeight = heightProp;
            }
        } catch(e) {}
    };

    setFrameHeight();

    const setup = () => {
        setFrameHeight();
        // ResizeObserver is not reliable. instead we do this
        const step = () => {
            setFrameHeight();
            window.requestAnimationFrame(step);
        };
        step();
    };

    if (frame.contentDocument.readyState === 'complete') {
        setup();
    } else {
        frame.addEventListener('load', () => {
            setup();
        });
    }

}