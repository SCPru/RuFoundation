export function makeTOC(node: HTMLElement) {

    // hack: mark node as already processed because it was
    if ((node as any)._toc) {
        return
    }
    (node as any)._toc = true;
    // end hack

    const hideButton: HTMLElement = node.querySelector('.w-toc-hide');
    const showButton: HTMLElement = node.querySelector('.w-toc-show');
    const list: HTMLElement = node.querySelector('.w-toc-content');

    hideButton.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        list.style.display = 'none';
        hideButton.style.display = 'none';
        showButton.style.display = '';
    });

    showButton.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        list.style.display = '';
        hideButton.style.display = '';
        showButton.style.display = 'none';
    });

}