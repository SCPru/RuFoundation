function getFrameByEvent(event) {
    return Array.from(document.getElementsByTagName('iframe')).filter(iframe => {
        return iframe.contentWindow === event.source;
    })[0];
}

window.addEventListener('message', (event) => {
    console.log('message event', event);
    if (event.data && event.data.type === 'iframe-change-height') {
        const { payload: { height, id } } = event.data;
        const frame = document.getElementById(id);
        if (!frame || frame.tagName.toLowerCase() !== 'iframe') {
            return
        }
        const heightProp = `${height}px`;
        if (frame.style.minHeight !== heightProp) {
            frame.style.minHeight = heightProp;
        }
    }
});
