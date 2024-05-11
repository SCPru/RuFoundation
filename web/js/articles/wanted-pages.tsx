import * as React from 'react';
import * as ReactDOM from 'react-dom';
import Loader from "../util/loader";
import {callModule, ModuleRenderResponse} from "../api/modules"
import {showErrorModal} from "../util/wikidot-modal";


export function makeWantedPages(node: HTMLElement) {

    // hack: mark node as already processed because it was
    if ((node as any)._wantedpages) {
        return
    }
    (node as any)._wantedpages = true;
    // end hack

    const wpBasePathParams = JSON.parse(node.dataset.wantedPagesPathParams!);
    const wpBaseParams = JSON.parse(node.dataset.wantedPagesParams!);
    const wpPageId = node.dataset.wantedPagesPageId;

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
            const { result: rendered } = await callModule<ModuleRenderResponse>({
                module: 'wantedpages',
                pageId: wpPageId,
                method: 'render',
                pathParams: Object.assign(wpBasePathParams, {p: page}),
                params: wpBaseParams,
            });
            ReactDOM.unmountComponentAtNode(loaderInto);
            loaderInto.innerHTML = '';
            loaderInto.style.display = 'none';
            const tmp = document.createElement('div');
            tmp.innerHTML = rendered;
            const newNode = tmp.firstElementChild!;
            node.parentNode!.replaceChild(newNode, node);
        } catch (e) {
            ReactDOM.unmountComponentAtNode(loaderInto);
            loaderInto.innerHTML = '';
            loaderInto.style.display = 'none';
            showErrorModal(e.error || 'Ошибка связи с сервером');
        }
    };

    // handle page switch
    const pagers = node.querySelectorAll(':scope > .pager');
    pagers.forEach(pager => pager.querySelectorAll<HTMLElement>('*[data-pagination-target]').forEach((node: HTMLElement) => {
        node.addEventListener('click', (e) => switchPage(e, node.dataset.paginationTarget!));
    }));

}