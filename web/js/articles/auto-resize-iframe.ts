window.addEventListener('message', (event) => {
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
