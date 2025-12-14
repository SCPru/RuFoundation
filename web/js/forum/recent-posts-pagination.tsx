import React from 'react'
import { renderTo, unmountFromRoot } from '~util/react-render-into'
import { callModule, ModuleRenderResponse } from '../api/modules'
import Loader from '../util/loader'
import { showErrorModal } from '../util/wikidot-modal'

export function makeRecentPosts(node: HTMLElement) {
  // hack: mark node as already processed because it was
  if ((node as any)._recentposts) {
    return
  }
  ;(node as any)._recentposts = true
  // end hack

  const rpBasePathParams = JSON.parse(node.dataset.recentPostsPathParams)
  const rpBaseParams = JSON.parse(node.dataset.recentPostsParams)

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
  node.appendChild(loaderInto)

  //
  const switchPage = async (e: MouseEvent, page: string, addParams: {}) => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    loaderInto.style.display = 'flex'
    // because our loader is React, we should display it like this.
    renderTo(loaderInto, <Loader size={80} borderSize={8} />)
    //
    try {
      const { result: rendered } = await callModule<ModuleRenderResponse>({
        module: 'recentposts',
        method: 'render',
        pathParams: Object.assign(rpBasePathParams, { p: page }, addParams),
        params: rpBaseParams,
      })
      unmountFromRoot(loaderInto)
      loaderInto.innerHTML = ''
      loaderInto.style.display = 'none'
      const tmp = document.createElement('div')
      tmp.innerHTML = rendered
      const newNode = tmp.firstElementChild
      node.parentNode.replaceChild(newNode, node)
    } catch (e) {
      unmountFromRoot(loaderInto)
      loaderInto.innerHTML = ''
      loaderInto.style.display = 'none'
      showErrorModal(e.error || 'Ошибка связи с сервером')
    }
  }

  // handle page switch
  const pagers = node.querySelectorAll(':scope > div > .thread-container > .pager')
  pagers.forEach(pager =>
    pager.querySelectorAll('*[data-pagination-target]').forEach((node: HTMLElement) => {
      node.addEventListener('click', e => switchPage(e, node.dataset.paginationTarget, {}))
    }),
  )

  // handle category change
  node.querySelector('.form input.btn')?.addEventListener('click', () => {
    const value = (node.querySelector('.form select') as HTMLSelectElement).value
    switchPage(null, '1', { c: value })
  })
}
