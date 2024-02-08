export function makeCollapsible(node: HTMLElement) {

    // hack: mark node as already processed because it was
    if ((node as any)._collapsible) {
        return
    }
    (node as any)._collapsible = true;
    // end hack

    const foldedElement: HTMLElement = node.querySelector('.collapsible-block-folded');
    const unfoldedElement: HTMLElement = node.querySelector('.collapsible-block-unfolded');

    const foldedLink: HTMLElement = foldedElement.querySelector('.collapsible-block-link');
    const unfoldedLinks: NodeListOf<HTMLElement> = unfoldedElement.querySelectorAll(':scope > .collapsible-block-unfolded-link > .collapsible-block-link');

    foldedLink.addEventListener('click', () => {
        unfoldedElement.style.display = 'block';
        foldedElement.style.display = 'none';
    });

    unfoldedLinks.forEach(unfoldedLink => unfoldedLink.addEventListener('click', () => {
        unfoldedElement.style.display = 'none';
        foldedElement.style.display = 'block';
    }));

}