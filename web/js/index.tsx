import * as React from 'react';
import * as ReactDOM from 'react-dom';
import Page404 from './entrypoints/page-404';
import PageOptions from "./entrypoints/page-options";
import {makeCollapsible} from "./articles/collapsible";


function renderTo(where: HTMLElement, what: any) {
    ReactDOM.render(what, where);

}


window.addEventListener('DOMContentLoaded', () => {

    document.querySelectorAll('#create-new-page').forEach((node: HTMLElement) => renderTo(node, <Page404 {...node.dataset} />));
    document.querySelectorAll('#w-page-options').forEach((node: HTMLElement) => renderTo(node, <PageOptions {...JSON.parse(node.dataset.config)} />));

    // enable collapsibles that loaded with HTML
    document.querySelectorAll('.collapsible-block').forEach((node: HTMLElement) => makeCollapsible(node));

    // establish watcher. will be used later for things like TabView too
    const observer = new MutationObserver((mutationList) => {
        mutationList.forEach(record => {
            if (record.type === 'childList') {
                record.addedNodes.forEach((node: HTMLElement) => {
                    if (node.classList && node.classList.contains('collapsible-block')) {
                        makeCollapsible(node);
                    }
                })
            }
        });
    });

    observer.observe(document.body);

});
