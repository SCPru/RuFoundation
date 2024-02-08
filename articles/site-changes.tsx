import * as React from 'react';
import * as ReactDOM from 'react-dom';
import Loader from "../util/loader";
import {callModule, ModuleRenderResponse} from "../api/modules"
import {showErrorModal} from "../util/wikidot-modal";


export function makeSiteChanges(node: HTMLElement) {

    // hack: mark node as already processed because it was
    if ((node as any)._sitechanges) {
        return
    }
    (node as any)._sitechanges = true;
    // end hack

    const scBasePathParams = JSON.parse(node.dataset.siteChangesPathParams);
    const scBaseParams = JSON.parse(node.dataset.siteChangesParams);

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
    const switchPage = async (e: MouseEvent, page: string, addParams: {}) => {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        loaderInto.style.display = 'flex';
        // because our loader is React, we should display it like this.
        ReactDOM.render(<Loader size={80} borderSize={8} />, loaderInto);
        //
        try {
            const { result: rendered } = await callModule<ModuleRenderResponse>({
                module: 'sitechanges',
                method: 'render',
                pathParams: Object.assign(scBasePathParams, {p: page}, addParams),
                params: scBaseParams
            });
            ReactDOM.unmountComponentAtNode(loaderInto);
            loaderInto.innerHTML = '';
            loaderInto.style.display = 'none';
            const tmp = document.createElement('div');
            tmp.innerHTML = rendered;
            const newNode = tmp.firstElementChild;
            node.parentNode.replaceChild(newNode, node);
        } catch (e) {
            ReactDOM.unmountComponentAtNode(loaderInto);
            loaderInto.innerHTML = '';
            loaderInto.style.display = 'none';
            showErrorModal(e.error || 'Ошибка связи с сервером');
        }
    };

    // handle page switch
    const pagers = node.querySelectorAll(':scope > .changes-list > .pager');
    pagers.forEach(pager => pager.querySelectorAll('*[data-pagination-target]').forEach((node: HTMLElement) => {
        node.addEventListener('click', (e) => switchPage(e, node.dataset.paginationTarget, {}));
    }));

    // handle type filters
    let allFilter = null;
    let typeFilters = [];
    node.querySelectorAll('.w-type-filter input').forEach((input: HTMLInputElement) => {
        if (input.name === '*') {
            allFilter = input;
        } else {
            typeFilters.push(input);
        }
    });

    allFilter.addEventListener('change', (e) => {
        if (!e.target.checked && !typeFilters.find(x => x.checked)) {
            e.target.checked = true;
            return;
        }
        if (e.target.checked) {
            typeFilters.forEach(filter => filter.checked = false);
        }
    });

    typeFilters.forEach(filter => {
        filter.addEventListener('change', (e) => {
            if (!e.target.checked && !typeFilters.find(x => x.checked)) {
                allFilter.checked = true;
                return;
            }
            allFilter.checked = false;
        });
    });

    node.querySelector('form input.btn')?.addEventListener('click', () => {
        const types = [];
        typeFilters.forEach(filter => {
            if (filter.checked) {
                types.push(filter.name);
            }
        });

        const category = (node.querySelector('#rev-category') as HTMLSelectElement).value;
        const perPage = (node.querySelector('#rev-perpage') as HTMLSelectElement).value;
        const userName = (node.querySelector('#rev-username') as HTMLInputElement).value;

        const addParams = {category, perPage, userName};
        typeFilters.forEach(filter => addParams[filter.name] = 'false');
        types.forEach(t => addParams[t] = 'true');

        switchPage(null, "1", addParams);
    });

}