import React from 'react'
import './articles/auto-resize-iframe'
import { makeCodeBlock } from './articles/codeblock'
import { makeCollapsible } from './articles/collapsible'
import { makeDate } from './articles/date'
import { makeFootnote } from './articles/footnote'
import { makeInterwiki } from './articles/interwiki'
import { makeListPages } from './articles/list-pages'
import { makeStarsRateModule } from './articles/rate-stars'
import { makeUpDownRateModule } from './articles/rate-updown'
import { makeRefForm } from './articles/ref-form'
import { makeSiteChanges } from './articles/site-changes'
import { makeTabView } from './articles/tabview'
import { makeTOC } from './articles/toc'
import { makeWantedPages } from './articles/wanted-pages'
import ForumNewPost from './entrypoints/forum-new-post'
import ForumNewThread from './entrypoints/forum-new-thread'
import ForumPostOptions from './entrypoints/forum-post-options'
import ForumThreadOptions from './entrypoints/forum-thread-options'
import { attachApiMessageListener } from './entrypoints/messages-api-interface'
import Page404 from './entrypoints/page-404'
import PageLoginStatus from './entrypoints/page-login-status'
import PageOptions from './entrypoints/page-options'
import { makeRecentPosts } from './forum/recent-posts-pagination'
import { makeForumThread } from './forum/thread-pagination'
import ReactivePage from './reactive/router'
import { makePasswordToggle } from './util/password'
import AdminSusUsers from './entrypoints/admin-sus-users'
import { renderTo } from '~util/react-render-into'

attachApiMessageListener()

window.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('#create-new-page').forEach((node: HTMLElement) => renderTo(node, <Page404 {...JSON.parse(node.dataset.config)} />))
  document
    .querySelectorAll('#page-options-container')
    .forEach((node: HTMLElement) => renderTo(node, <PageOptions {...JSON.parse(node.dataset.config)} />))
  document.querySelectorAll('#login-status').forEach((node: HTMLElement) => renderTo(node, <PageLoginStatus {...JSON.parse(node.dataset.config)} />))
  document
    .querySelectorAll('.w-forum-new-thread')
    .forEach((node: HTMLElement) => renderTo(node, <ForumNewThread {...JSON.parse(node.dataset.config)} />))
  document.querySelectorAll('.w-forum-new-post').forEach((node: HTMLElement) => renderTo(node, <ForumNewPost {...JSON.parse(node.dataset.config)} />))
  document
    .querySelectorAll('.w-forum-thread-options')
    .forEach((node: HTMLElement) => renderTo(node, <ForumThreadOptions {...JSON.parse(node.dataset.config)} />))

  makePasswordToggle()

  // add new things here!
  const processNode = (node: HTMLElement) => {
    try {
      if (!node.classList || node.classList.contains('w-fake-node')) return
      if (node.classList.contains('w-collapsible')) {
        makeCollapsible(node)
      } else if (node.classList.contains('w-tabview')) {
        makeTabView(node)
      } else if (node.classList.contains('w-rate-module')) {
        makeUpDownRateModule(node)
      } else if (node.classList.contains('w-stars-rate-module')) {
        makeStarsRateModule(node)
      } else if (node.classList.contains('w-list-pages')) {
        makeListPages(node)
      } else if (node.classList.contains('w-wanted-pages')) {
        makeWantedPages(node)
      } else if (node.classList.contains('w-toc')) {
        makeTOC(node)
      } else if (node.classList.contains('w-forum-post-options')) {
        renderTo(node, <ForumPostOptions {...JSON.parse(node.dataset.config)} />)
      } else if (node.classList.contains('w-forum-thread')) {
        makeForumThread(node)
      } else if (node.classList.contains('w-forum-recent-posts')) {
        makeRecentPosts(node)
      } else if (node.classList.contains('w-site-changes')) {
        makeSiteChanges(node)
      } else if (node.classList.contains('w-date')) {
        makeDate(node)
      } else if (node.classList.contains('w-footnoteref')) {
        makeFootnote(node)
      } else if (node.classList.contains('w-code')) {
        makeCodeBlock(node)
      } else if (node.classList.contains('w-ref-form')) {
        makeRefForm(node)
      } else if (node.classList.contains('w-interwiki')) {
        makeInterwiki(node)
      } else if (node.classList.contains('w-admin-sus-users')) {
        renderTo(node, <AdminSusUsers />)
      }
    } catch (e) {
      console.error('Failed to process node', node, e)
    }
  }

  // enable collapsibles that loaded with HTML
  document.querySelectorAll('*').forEach((node: HTMLElement) => {
    if (node.nodeType === Node.ELEMENT_NODE) {
      processNode(node)
    }
  })

  const reactiveRoot: HTMLElement = document.querySelector('#reactive-root')
  if (reactiveRoot) {
    renderTo(reactiveRoot, <ReactivePage />)
  }

  // establish watcher. will be used later for things like TabView too
  const observer = new MutationObserver(mutationList => {
    mutationList.forEach(record => {
      if (record.type === 'childList') {
        record.addedNodes.forEach((node: HTMLElement) => {
          if (node.nodeType !== Node.ELEMENT_NODE) {
            return
          }
          processNode(node)
          node.querySelectorAll('*').forEach((subnode: HTMLElement) => {
            if (subnode.nodeType === Node.ELEMENT_NODE) {
              processNode(subnode)
            }
          })
        })
      } else if (record.type === 'attributes') {
        if (record.attributeName === 'class' && record.target) {
          processNode(record.target as HTMLElement)
        }
      }
    })
  })

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  })
})
