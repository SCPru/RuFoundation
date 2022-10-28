import hljs from 'highlight.js';


export function makeCodeBlock(node: HTMLElement) {

    // hack: mark node as already processed because it was
    if ((node as any)._blockcode) {
        return
    }
    (node as any)._blockcode = true;
    // end hack

    hljs.highlightElement(node);
}