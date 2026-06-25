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

interface DateAnchor {
  postId: number
  page: number
  label: string
  title: string
  position: number
}

interface ForumPostCreatedEventDetail {
  url: string
  handled?: boolean
}

function getPostIdFromHash(hash = window.location.hash) {
  const match = hash.match(/^#post-(\d+)$/)
  return match ? match[1] : null
}

function getPostIdFromUrl(rawUrl: string) {
  try {
    return getPostIdFromHash(new URL(rawUrl, window.location.origin).hash)
  } catch {
    return null
  }
}

function getThreadIdFromUrl(rawUrl: string) {
  try {
    const match = new URL(rawUrl, window.location.origin).pathname.match(/\/forum\/t-(\d+)/)
    return match ? match[1] : null
  } catch {
    return null
  }
}

function parseInteger(value: string | undefined, fallback: number) {
  const parsed = parseInt(value || '', 10)
  return Number.isFinite(parsed) ? parsed : fallback
}

function parseDateAnchors(node: HTMLElement): Array<DateAnchor> {
  try {
    const anchors = JSON.parse(node.dataset.forumThreadDateAnchors || '[]')
    return Array.isArray(anchors) ? anchors : []
  } catch {
    return []
  }
}

export function makeForumThread(node: HTMLElement) {
  // hack: mark node as already processed because it was
  if ((node as any)._forumthread) {
    return
  }
  ;(node as any)._forumthread = true
  // end hack

  let fBasePathParams = JSON.parse(node.dataset.forumThreadPathParams!)
  let fBaseParams = JSON.parse(node.dataset.forumThreadParams!)
  let displayMode = node.dataset.forumThreadMode === 'infinite' ? 'infinite' : 'pagination'
  let sortOrder = node.dataset.forumThreadSortOrder === 'newest' ? 'newest' : 'oldest'
  let currentPage = parseInteger(node.dataset.forumThreadCurrentPage || fBasePathParams.p, 1)
  let maxPage = parseInteger(node.dataset.forumThreadMaxPage, 1)
  let dateAnchors = parseDateAnchors(node)
  let loadedPages = new Set<number>([currentPage])
  let isInfiniteLoading = false
  let infiniteObserver: IntersectionObserver | null = null

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

  const refreshStateFromNode = (source: HTMLElement = node) => {
    fBasePathParams = JSON.parse(source.dataset.forumThreadPathParams!)
    fBaseParams = JSON.parse(source.dataset.forumThreadParams!)
    displayMode = source.dataset.forumThreadMode === 'infinite' ? 'infinite' : 'pagination'
    sortOrder = source.dataset.forumThreadSortOrder === 'newest' ? 'newest' : 'oldest'
    currentPage = parseInteger(source.dataset.forumThreadCurrentPage || fBasePathParams.p, 1)
    maxPage = parseInteger(source.dataset.forumThreadMaxPage, 1)
    dateAnchors = parseDateAnchors(source)
  }

  const applyThreadDataset = (source: HTMLElement) => {
    node.dataset.forumThreadPathParams = source.dataset.forumThreadPathParams
    node.dataset.forumThreadParams = source.dataset.forumThreadParams
    node.dataset.forumThreadMode = source.dataset.forumThreadMode
    node.dataset.forumThreadSortOrder = source.dataset.forumThreadSortOrder
    node.dataset.forumThreadCurrentPage = source.dataset.forumThreadCurrentPage
    node.dataset.forumThreadMaxPage = source.dataset.forumThreadMaxPage
    node.dataset.forumThreadTotalPosts = source.dataset.forumThreadTotalPosts
    node.dataset.forumThreadDateAnchors = source.dataset.forumThreadDateAnchors
    refreshStateFromNode()
  }

  const setPageLoading = (loading: boolean) => {
    node.classList.toggle('is-loading', loading)
    loaderInto.style.display = loading ? 'flex' : 'none'

    if (loading) {
      renderTo(loaderInto, <Loader size={80} borderSize={8} />)
    } else {
      unmountFromRoot(loaderInto)
      loaderInto.innerHTML = ''
    }
  }

  const scrollToPost = (postId?: string | null) => {
    if (!postId) {
      return
    }

    window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => {
        const target = document.getElementById(`post-${postId}`)
        if (!target) {
          return
        }
        target.scrollIntoView({ behavior: 'smooth', block: 'start' })
        target.classList.add('forum-post-focus')
        window.setTimeout(() => target.classList.remove('forum-post-focus'), 1400)
      })
    })
  }

  const hasLoadedPost = (postId?: string | null) => {
    return postId ? document.getElementById(`post-${postId}`) !== null : false
  }

  const navigateToLoadedPost = (postId?: string | null, updateHash = true) => {
    if (!hasLoadedPost(postId)) {
      return false
    }

    if (updateHash) {
      const nextHash = `#post-${postId}`
      if (window.location.hash !== nextHash) {
        window.history.pushState(
          {
            ...(window.history.state || {}),
            forumThread: fBasePathParams.t,
            forumThreadPage: fBasePathParams.p || String(currentPage),
          },
          '',
          nextHash,
        )
      }
    }

    scrollToPost(postId)
    return true
  }

  const navigateToPost = (postId?: string | null) => {
    if (!postId || navigateToLoadedPost(postId)) {
      return
    }
    switchPage(null, { postId })
  }

  const animateInsertedPosts = (posts: Array<Element>) => {
    posts.forEach(post => post.classList.add('forum-post-enter'))
    window.requestAnimationFrame(() => {
      posts.forEach(post => post.classList.add('is-visible'))
      window.setTimeout(() => {
        posts.forEach(post => post.classList.remove('forum-post-enter', 'is-visible'))
      }, 260)
    })
  }

  const buildPathParams = (config: SwitchPageConfig) => {
    const pathParams = Object.assign({}, fBasePathParams)
    if (config.page !== undefined) {
      pathParams.p = config.page
      delete pathParams.post
    }
    if (config.postId !== undefined) {
      pathParams.post = config.postId
      delete pathParams.p
    }
    return pathParams
  }

  const renderThreadPage = async (config: SwitchPageConfig) => {
    const { result: rendered } = await callModule<ModuleRenderResponse>({
      module: 'forumthread',
      method: 'render',
      pathParams: buildPathParams(config),
      params: Object.assign({}, fBaseParams, {
        contentOnly: 'yes',
        displayMode,
        sortOrder,
      }),
    })
    const tmp = document.createElement('div')
    tmp.innerHTML = rendered
    return tmp.firstElementChild as HTMLElement
  }

  const updateUrl = (newNode: HTMLElement, config: SwitchPageConfig) => {
    if (config.isFromHistory) {
      return
    }

    const fNewPathParams = JSON.parse(newNode.dataset.forumThreadPathParams!)
    let newUrl = `/forum/t-${fNewPathParams.t}`
    for (const k in fNewPathParams) {
      if (k === 'p' || k === 't' || k === 'post' || fNewPathParams[k] === null) {
        continue
      }
      newUrl += `/${encodeURIComponent(k)}/${encodeURIComponent(fNewPathParams[k])}`
    }
    newUrl += `/p/${fNewPathParams.p}`
    const nextHash = config.postId ? `#post-${config.postId}` : window.location.hash
    window.history.pushState({ forumThread: fNewPathParams.t, forumThreadPage: fNewPathParams.p }, '', newUrl + nextHash)
  }

  const removeInfiniteUi = () => {
    infiniteObserver?.disconnect()
    infiniteObserver = null
    node.querySelectorAll(':scope > .forum-infinite-sentinel, :scope > .forum-date-rail').forEach(item => item.remove())
  }

  const getNextInfinitePage = () => {
    for (let page = Math.max(...Array.from(loadedPages)) + 1; page <= maxPage; page++) {
      if (!loadedPages.has(page)) {
        return page
      }
    }
    return null
  }

  const getPreviousInfinitePage = () => {
    for (let page = Math.min(...Array.from(loadedPages)) - 1; page >= 1; page--) {
      if (!loadedPages.has(page)) {
        return page
      }
    }
    return null
  }

  const loadInfinitePage = async (page: number, direction: 'append' | 'prepend') => {
    if (isInfiniteLoading || loadedPages.has(page) || page < 1 || page > maxPage) {
      return
    }

    isInfiniteLoading = true
    const sentinel = node.querySelector(`:scope > .forum-infinite-sentinel[data-direction="${direction}"]`) as HTMLElement | null
    sentinel?.classList.add('is-loading')
    if (sentinel) {
      renderTo(sentinel, <Loader size={36} borderSize={4} />)
    }

    try {
      const newNode = await renderThreadPage({ page: String(page) })
      applyThreadDataset(newNode)
      loadedPages.add(page)

      const postsRoot = node.querySelector('#thread-container-posts')
      const newPostsRoot = newNode.querySelector('#thread-container-posts')
      const newPosts = newPostsRoot ? Array.from(newPostsRoot.children).filter(child => !child.classList.contains('pager')) : []

      if (postsRoot && newPosts.length) {
        const scrollAnchor = direction === 'prepend' ? (postsRoot.firstElementChild as HTMLElement | null) : null
        const anchorTop = scrollAnchor?.getBoundingClientRect().top ?? 0

        if (direction === 'prepend') {
          const fragment = document.createDocumentFragment()
          newPosts.forEach(post => fragment.appendChild(post))
          postsRoot.insertBefore(fragment, postsRoot.firstChild)
          if (scrollAnchor) {
            window.scrollBy({ top: scrollAnchor.getBoundingClientRect().top - anchorTop, behavior: 'auto' })
          }
        } else {
          newPosts.forEach(post => postsRoot.appendChild(post))
        }
        animateInsertedPosts(newPosts)
      }
    } catch (e) {
      showErrorModal(e.error || 'Ошибка связи с сервером')
    } finally {
      isInfiniteLoading = false
      if (sentinel) {
        unmountFromRoot(sentinel)
        sentinel.innerHTML = '<span>Загрузить ещё</span>'
        sentinel.classList.remove('is-loading')
      }
      setupInfiniteScroll()
    }
  }

  const getAnchorFromPointer = (e: PointerEvent, rail: HTMLElement) => {
    if (!dateAnchors.length) {
      return null
    }

    const rect = rail.getBoundingClientRect()
    const isHorizontal = window.matchMedia('(max-width: 720px)').matches
    const rawPosition = isHorizontal ? (e.clientX - rect.left) / rect.width : (e.clientY - rect.top) / rect.height
    const position = Math.max(0, Math.min(1, rawPosition))

    return dateAnchors.reduce((nearest, anchor) => {
      return Math.abs(anchor.position - position) < Math.abs(nearest.position - position) ? anchor : nearest
    }, dateAnchors[0])
  }

  const renderDateRail = () => {
    if (displayMode !== 'infinite' || dateAnchors.length < 2) {
      return
    }

    const rail = document.createElement('div')
    rail.className = 'forum-date-rail'
    rail.setAttribute('aria-label', 'Навигация по датам сообщений')

    const track = document.createElement('div')
    track.className = 'forum-date-rail-track'
    rail.appendChild(track)

    const label = document.createElement('div')
    label.className = 'forum-date-rail-label'
    rail.appendChild(label)

    let isDragging = false
    const showAnchor = (anchor: DateAnchor | null) => {
      if (!anchor) {
        rail.classList.remove('is-previewing')
        return
      }
      label.textContent = anchor.label
      label.style.setProperty('--forum-date-position', `${anchor.position * 100}%`)
      rail.classList.add('is-previewing')
    }

    dateAnchors.forEach(anchor => {
      const marker = document.createElement('button')
      marker.className = 'forum-date-rail-marker'
      marker.type = 'button'
      marker.setAttribute('aria-label', anchor.title)
      marker.style.setProperty('--forum-date-position', `${anchor.position * 100}%`)
      marker.addEventListener('click', e => {
        e.preventDefault()
        if (e.detail !== 0) {
          return
        }
        navigateToPost(String(anchor.postId))
      })
      rail.appendChild(marker)
    })

    rail.addEventListener('pointerdown', e => {
      isDragging = true
      rail.classList.add('is-dragging')
      rail.setPointerCapture(e.pointerId)
      showAnchor(getAnchorFromPointer(e, rail))
    })
    rail.addEventListener('pointermove', e => {
      if (isDragging || e.pointerType === 'mouse') {
        showAnchor(getAnchorFromPointer(e, rail))
      }
    })
    rail.addEventListener('pointerleave', () => {
      if (!isDragging) {
        showAnchor(null)
      }
    })
    rail.addEventListener('pointerup', e => {
      if (!isDragging) {
        return
      }
      const anchor = getAnchorFromPointer(e, rail)
      isDragging = false
      rail.classList.remove('is-dragging')
      showAnchor(null)
      if (anchor) {
        navigateToPost(String(anchor.postId))
      }
    })
    rail.addEventListener('pointercancel', () => {
      isDragging = false
      rail.classList.remove('is-dragging')
      showAnchor(null)
    })

    node.appendChild(rail)
  }

  const setupInfiniteScroll = () => {
    removeInfiniteUi()
    if (displayMode !== 'infinite') {
      return
    }

    renderDateRail()

    const postsRoot = node.querySelector('#thread-container-posts')
    const previousPage = getPreviousInfinitePage()
    if (previousPage && postsRoot) {
      const sentinel = document.createElement('button')
      sentinel.className = 'forum-infinite-sentinel is-before'
      sentinel.dataset.direction = 'prepend'
      sentinel.type = 'button'
      sentinel.innerHTML = '<span>Загрузить предыдущие</span>'
      sentinel.addEventListener('click', e => {
        e.preventDefault()
        loadInfinitePage(previousPage, 'prepend')
      })
      node.insertBefore(sentinel, postsRoot)
    }

    const nextPage = getNextInfinitePage()
    if (nextPage) {
      const sentinel = document.createElement('button')
      sentinel.className = 'forum-infinite-sentinel is-after'
      sentinel.dataset.direction = 'append'
      sentinel.type = 'button'
      sentinel.innerHTML = '<span>Загрузить ещё</span>'
      sentinel.addEventListener('click', e => {
        e.preventDefault()
        loadInfinitePage(nextPage, 'append')
      })
      node.appendChild(sentinel)
    }

    if ('IntersectionObserver' in window) {
      infiniteObserver = new IntersectionObserver(
        entries => {
          const visibleEntry = entries.find(entry => entry.isIntersecting)
          const direction = (visibleEntry?.target as HTMLElement | undefined)?.dataset.direction
          if (direction === 'prepend' && previousPage) {
            loadInfinitePage(previousPage, 'prepend')
          }
          if (direction === 'append' && nextPage) {
            loadInfinitePage(nextPage, 'append')
          }
        },
        { rootMargin: '420px 0px' },
      )
      node.querySelectorAll(':scope > .forum-infinite-sentinel').forEach(sentinel => infiniteObserver?.observe(sentinel))
    }
  }

  const setupPageSwitch = () => {
    removeInfiniteUi()
    // handle page switch
    const pagers = node.querySelectorAll(':scope > div > .pager')
    pagers.forEach(pager =>
      pager.querySelectorAll('*[data-pagination-target]').forEach((node: HTMLElement) => {
        node.addEventListener('click', e => switchPage(e, { page: node.dataset.paginationTarget }))
      }),
    )
    //
    node.appendChild(loaderInto)
    setupInfiniteScroll()
  }

  const onPostLinkClick = (e: MouseEvent) => {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) {
      return
    }

    const target = e.target
    if (!(target instanceof Element)) {
      return
    }

    const link = target.closest('a[href]') as HTMLAnchorElement | null
    if (!link || !node.contains(link)) {
      return
    }

    const postId = getPostIdFromUrl(link.href)
    if (!postId) {
      return
    }

    const threadId = getThreadIdFromUrl(link.href)
    if (threadId && String(threadId) !== String(fBasePathParams.t)) {
      return
    }

    e.preventDefault()
    e.stopPropagation()
    navigateToPost(postId)
  }

  //
  const switchPage = async (e: MouseEvent | null, config: SwitchPageConfig) => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    setPageLoading(true)
    //
    try {
      const newNode = await renderThreadPage(config)
      setPageLoading(false)
      node.innerHTML = newNode.innerHTML
      applyThreadDataset(newNode)
      loadedPages = new Set<number>([currentPage])
      setupPageSwitch()
      scrollToPost(config.postId)
      updateUrl(newNode, config)
    } catch (e) {
      setPageLoading(false)
      showErrorModal(e.error || 'Ошибка связи с сервером')
    }
  }

  window.addEventListener('popstate', (e: PopStateEvent) => {
    if (e.state && e.state.forumThread === fBasePathParams.t) {
      switchPage(null, { page: e.state.forumThreadPage, isFromHistory: true })
    }
  })

  window.addEventListener('hashchange', () => {
    const postId = getPostIdFromHash()
    if (postId) {
      if (navigateToLoadedPost(postId, false)) {
        return
      }
      // navigate to different post; ignore page
      switchPage(null, { postId })
    }
  })

  window.addEventListener('forum:post-created', (e: Event) => {
    const event = e as CustomEvent<ForumPostCreatedEventDetail>
    const postId = getPostIdFromUrl(event.detail?.url || '')
    const threadId = getThreadIdFromUrl(event.detail?.url || '')
    if (!postId || (threadId && String(threadId) !== String(fBasePathParams.t))) {
      return
    }
    event.detail.handled = true
    navigateToPost(postId)
  })

  // due to wikidot's shitty way of doing direct post links, we have to detect it here.
  // if this is a direct post link, produce a pagination query with the post ID taken from hash
  const initialPostId = getPostIdFromHash()
  node.addEventListener('click', onPostLinkClick)
  setupPageSwitch()
  if (initialPostId) {
    navigateToPost(initialPostId)
  }
}
