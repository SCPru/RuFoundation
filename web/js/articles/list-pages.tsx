import * as React from 'react';
import * as ReactDOM from 'react-dom';
import Loader from "../util/loader";
import {callModule} from "../api/modules";
import {showErrorModal} from "../util/wikidot-modal";


export function makeListPages(node: HTMLElement) {

    // hack: mark node as already processed because it was
    if ((node as any)._listpages) {
        return
    }
    (node as any)._listpages = true;
    // end hack

    const lpBasePathParams = JSON.parse(node.dataset.listPagesPathParams);
    const lpBaseParams = JSON.parse(node.dataset.listPagesParams);
    const lpBaseContent = JSON.parse(node.dataset.listPagesContent);
    const lpPageId = node.dataset.listPagesPageId;

    // display loader when needed.
    const loaderInto = document.createElement('div');
    Object.assign(loaderInto.style, {
        position: 'absolute',
        left: '0px',
        right: '0px',
        top: '0px',
        bottom: '-1px',
        display: 'none',
        background: '#7777777f',
        alignItems: 'center',
        justifyContent: 'center',
        boxSizing: 'border-box'
    });
    node.appendChild(loaderInto);

    //
    const switchPage = async (e: MouseEvent, page: string) => {
        e.preventDefault();
        e.stopPropagation();
        loaderInto.style.display = 'flex';
        // because our loader is React, we should display it like this.
        ReactDOM.render(<Loader size={80} borderSize={8} />, loaderInto);
        //
        try {
            const { result: rendered } = await callModule({
                module: 'listpages',
                pageId: lpPageId,
                method: 'render',
                pathParams: Object.assign(lpBasePathParams, {p: page}),
                params: lpBaseParams,
                content: lpBaseContent
            });
            ReactDOM.unmountComponentAtNode(loaderInto);
            loaderInto.innerHTML = '';
            loaderInto.style.display = 'none';
            const tmp = document.createElement('div');
            tmp.innerHTML = rendered;
            node.parentNode.replaceChild(tmp.firstElementChild, node);
        } catch (e) {
            ReactDOM.unmountComponentAtNode(loaderInto);
            loaderInto.innerHTML = '';
            loaderInto.style.display = 'none';
            showErrorModal(e.error || '???????????? ?????????? ?? ????????????????');
        }
    };

    // handle page switch
    const pager = node.querySelector('.pager');
    pager?.querySelectorAll('*[data-pagination-target]').forEach((node: HTMLElement) => {
        node.addEventListener('click', (e) => switchPage(e, node.dataset.paginationTarget));
    });

}