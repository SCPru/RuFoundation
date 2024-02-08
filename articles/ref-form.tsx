export function makeRefForm(node: HTMLElement) {

    // hack: mark node as already processed because it was
    if ((node as any)._refForm) {
        return
    }
    (node as any)._refForm = true;
    // end hack

    node.addEventListener('submit', e => {
        e.preventDefault();
        e.stopPropagation();

        if (!node.dataset.targetPage) {
            return;
        }

        // find all inputs within the form. convert to path params, send.
        let target = `/${node.dataset.targetPage}`

        node.querySelectorAll('input').forEach(input => {
            if (input instanceof HTMLInputElement) {
                if (!input.name) {
                    return;
                }
                target += `/${encodeURIComponent(input.name)}/${encodeURIComponent(input.value)}`;
            }
        });

        if (window.location.pathname === target) {
            window.location.reload();
        } else {
            window.location.pathname = target;
        }
    });

}