import * as React from 'react';
import * as ReactDOM from 'react-dom';
import Page404 from './entrypoints/page-404';
import PageOptions from "./entrypoints/page-options";
import {makeCollapsible} from "./articles/collapsible";
import {makeTabView} from "./articles/tabview";
import {makeRateModule} from "./articles/rate";
import "./articles/auto-resize-iframe";


function renderTo(where: HTMLElement, what: any) {
    ReactDOM.render(what, where);

}


window.addEventListener('DOMContentLoaded', () => {

    document.querySelectorAll('#create-new-page').forEach((node: HTMLElement) => renderTo(node, <Page404 {...node.dataset} />));
    document.querySelectorAll('#page-options-container').forEach((node: HTMLElement) => renderTo(node, <PageOptions {...JSON.parse(node.dataset.config)} />));

    // enable collapsibles that loaded with HTML
    document.querySelectorAll('.w-collapsible').forEach((node: HTMLElement) => makeCollapsible(node));
    document.querySelectorAll('.w-tabview').forEach((node: HTMLElement) => makeTabView(node));
    document.querySelectorAll('.w-rate-module').forEach((node: HTMLElement) => makeRateModule(node));

    // establish watcher. will be used later for things like TabView too
    const observer = new MutationObserver((mutationList) => {
        mutationList.forEach(record => {
            if (record.type === 'childList') {
                record.addedNodes.forEach((node: HTMLElement) => {
                    if (!node.classList) return;
                    if (node.classList.contains('w-collapsible')) {
                        makeCollapsible(node);
                    } else if (node.classList.contains('w-tabview')) {
                        makeTabView(node);
                    } else if (node.classList.contains('w-rate-module')) {
                        makeRateModule(node);
                    }
                })
            }
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

});
