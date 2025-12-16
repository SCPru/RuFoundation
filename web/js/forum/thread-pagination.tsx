import React from 'react'
import { renderTo, unmountFromRoot } from '~util/react-render-into'
import { callModule, ModuleRenderResponse } from '../api/modules'
import Loader from '../util/loader'
import { showErrorModal } from '../util/wikidot-modal'

// this code is brainless self-plagiarism off ListPages pagination, but with different module parameters
// page switching is made differently (no node self-replace) because this does not work nicely with history/state.

interface SwitchPageConfig {
  page?: string
  postId?: string
  isFromHistory?: boolean
}

export function makeForumThread(node: HTMLElement) {
  // hack: mark node as already processed because it was
  if ((node as any)._forumthread) {
    return
  }
  ;(node as any)._forumthread = true
  // end hack

  const fBasePathParams = JSON.parse(node.dataset.forumThreadPathParams!)
  const fBaseParams = JSON.parse(node.dataset.forumThreadParams!)

  window.history.replaceState({ forumThread: fBasePathParams.t, forumThreadPage: fBasePathParams.p || '1' }, '')

  // display loader when needed.
  const loaderInto = document.createElement('div')
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
    boxSizing: 'border-box',
  })

  const setupPageSwitch = () => {
    // handle page switch
    const pagers = node.querySelectorAll(':scope > div > .pager')
    pagers.forEach(pager =>
      pager.querySelectorAll('*[data-pagination-target]').forEach((node: HTMLElement) => {
        node.addEventListener('click', e => switchPage(e, { page: node.dataset.paginationTarget }))
      }),
    )
    //
    node.appendChild(loaderInto)
  }

  //
  const switchPage = async (e: MouseEvent | null, config: SwitchPageConfig) => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    loaderInto.style.display = 'flex'
    // because our loader is React, we should display it like this.
    renderTo(loaderInto, <Loader size={80} borderSize={8} />)
    //
    try {
      const pathParams = Object.assign({}, fBasePathParams)
      if (config.page !== undefined) {
        pathParams.p = config.page
      }
      if (config.postId !== undefined) {
        pathParams.post = config.postId
        delete pathParams.p
      }
      const { result: rendered } = await callModule<ModuleRenderResponse>({
        module: 'forumthread',
        method: 'render',
        pathParams: pathParams,
        params: Object.assign({}, fBaseParams, { contentOnly: 'yes' }),
      })
      unmountFromRoot(loaderInto)
      loaderInto.innerHTML = ''
      loaderInto.style.display = 'none'
      const tmp = document.createElement('div')
      tmp.innerHTML = rendered
      const newNode = tmp.firstElementChild as HTMLElement
      node.innerHTML = newNode.innerHTML
      setupPageSwitch()
      // rewrite URL so that users can easily copy-paste specific thread page from the address bar
      let newUrl
      if (!config.isFromHistory) {
        // take new page ID from the response
        const fNewPathParams = JSON.parse(newNode.dataset.forumThreadPathParams!)
        newUrl = `/forum/t-${fNewPathParams.t}`
        for (const k in fNewPathParams) {
          if (k === 'p' || k === 't' || k === 'post' || fNewPathParams[k] === null) {
            continue
          }
          newUrl += `/${encodeURIComponent(k)}/${encodeURIComponent(fNewPathParams[k])}`
        }
        newUrl += `/p/${fNewPathParams.p}`
        window.history.pushState({ forumThread: fNewPathParams.t, forumThreadPage: fNewPathParams.p }, '', newUrl + window.location.hash)
      }
    } catch (e) {
      unmountFromRoot(loaderInto)
      loaderInto.innerHTML = ''
      loaderInto.style.display = 'none'
      showErrorModal(e.error || 'Ошибка связи с сервером')
    }
  }

  window.addEventListener('popstate', (e: PopStateEvent) => {
    if (e.state && e.state.forumThread === fBasePathParams.t) {
      switchPage(null, { page: e.state.forumThreadPage, isFromHistory: true })
    }
  })

  window.addEventListener('hashchange', () => {
    if (window.location.hash.startsWith('#post-')) {
      // navigate to different post; ignore page
      switchPage(null, { postId: window.location.hash.substring(6) })
    }
  })

  // due to wikidot's shitty way of doing direct post links, we have to detect it here.
  // if this is a direct post link, erase any inner HTML and produce a pagination query with the post ID taken from hash
  if (window.location.hash.startsWith('#post-')) {
    node.innerHTML = ''
    setupPageSwitch()
    switchPage(null, { postId: window.location.hash.substring(6) })
  } else {
    setupPageSwitch()
  }
}
