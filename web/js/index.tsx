import * as React from 'react';
import * as ReactDOM from 'react-dom';
import Page404 from './entrypoints/page-404';
import PageOptions from "./entrypoints/page-options";


function renderTo(where: HTMLElement, what: any) {
    ReactDOM.render(what, where);

}


window.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('#create-new-page').forEach((node: HTMLElement) => renderTo(node, <Page404 {...node.dataset} />));
    document.querySelectorAll('#w-page-options').forEach((node: HTMLElement) => renderTo(node, <PageOptions {...JSON.parse(node.dataset.config)} />));
});
