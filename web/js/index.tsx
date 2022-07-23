import * as React from 'react';
import * as ReactDOM from 'react-dom';
import Page404 from './entrypoints/page-404';
import PageOptions from "./entrypoints/page-options";
import {makeCollapsible} from "./articles/collapsible";
import {makeTabView} from "./articles/tabview";
import {makeUpDownRateModule} from "./articles/rate-updown";
import {makeStarsRateModule} from "./articles/rate-stars";
import "./articles/auto-resize-iframe";
import {makeListPages} from "./articles/list-pages";
import {makePasswordToggle} from "./util/password";
import PageLoginStatus from "./entrypoints/page-login-status";


function renderTo(where: HTMLElement, what: any) {
    ReactDOM.render(what, where);

}


window.addEventListener('DOMContentLoaded', () => {

    document.querySelectorAll('#create-new-page').forEach((node: HTMLElement) => renderTo(node, <Page404 {...node.dataset} />));
    document.querySelectorAll('#page-options-container').forEach((node: HTMLElement) => renderTo(node, <PageOptions {...JSON.parse(node.dataset.config)} />));
    document.querySelectorAll('#login-status').forEach((node: HTMLElement) => renderTo(node, <PageLoginStatus {...JSON.parse(node.dataset.config)} />));

    makePasswordToggle();

    // add new things here!
    const processNode = (node: HTMLElement) => {
        if (!node.classList) return;
        if (node.classList.contains('w-collapsible')) {
            makeCollapsible(node);
        } else if (node.classList.contains('w-tabview')) {
            makeTabView(node);
        } else if (node.classList.contains('w-rate-module')) {
            makeUpDownRateModule(node);
        } else if (node.classList.contains('w-stars-rate-module')) {
            makeStarsRateModule(node);
        } else if (node.classList.contains('w-list-pages')) {
            makeListPages(node);
        }
    };

    // enable collapsibles that loaded with HTML
    document.querySelectorAll('*').forEach((node: HTMLElement) => {
        if (node.nodeType === Node.ELEMENT_NODE) {
            processNode(node);
        }
    });

    // establish watcher. will be used later for things like TabView too
    const observer = new MutationObserver((mutationList) => {
        mutationList.forEach(record => {
            if (record.type === 'childList') {
                record.addedNodes.forEach((node: HTMLElement) => {
                    if (node.nodeType !== Node.ELEMENT_NODE) {
                        return;
                    }
                    processNode(node);
                    node.querySelectorAll('*').forEach((subnode: HTMLElement) => {
                        if (subnode.nodeType === Node.ELEMENT_NODE) {
                            processNode(subnode);
                        }
                    });
                })
            } else if (record.type === 'attributes') {
                if (record.attributeName === 'class' && record.target) {
                    processNode(record.target as HTMLElement);
                }
            }
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

});
