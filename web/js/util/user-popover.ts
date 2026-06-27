import { makeCustomTooltips } from './tooltip'

interface ActivePopover {
  anchor: HTMLElement
  tooltip: HTMLElement
  userId: string
  closeTimer: number | null
  update: () => void
}

interface ModerateResponse {
  ok: boolean
  message?: string
  preview?: string
  errors?: Record<string, unknown>
}

const OPEN_DELAY = 120
const CLOSE_DELAY = 220
const POPOVER_MARGIN = 8
const POPOVER_GAP = 7
const htmlCache = new Map<string, string>()

let activePopover: ActivePopover | null = null
let openTimer: number | null = null

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}

function userPreviewUrl(anchor: HTMLElement) {
  const userId = anchor.dataset.userId
  const username = anchor.dataset.userName || 'user'
  return `/-/users/${userId}-${encodeURIComponent(username)}/preview`
}

function isCoarsePointer() {
  return window.matchMedia('(hover: none), (pointer: coarse)').matches
}

function clearOpenTimer() {
  if (openTimer !== null) {
    window.clearTimeout(openTimer)
    openTimer = null
  }
}

function clearCloseTimer(popover: ActivePopover | null) {
  if (popover && popover.closeTimer !== null) {
    window.clearTimeout(popover.closeTimer)
    popover.closeTimer = null
  }
}

function placeUserPopover(anchor: HTMLElement, tooltip: HTMLElement) {
  const viewportWidth = document.documentElement.clientWidth
  const viewportHeight = document.documentElement.clientHeight
  const anchorRect = anchor.getBoundingClientRect()

  tooltip.style.maxHeight = ''
  tooltip.style.overflowY = ''
  tooltip.style.visibility = 'hidden'
  tooltip.style.left = '0px'
  tooltip.style.top = '0px'

  let tooltipRect = tooltip.getBoundingClientRect()
  const availableBelow = viewportHeight - anchorRect.bottom - POPOVER_GAP - POPOVER_MARGIN
  const availableAbove = anchorRect.top - POPOVER_GAP - POPOVER_MARGIN
  const fitsBelow = tooltipRect.height <= availableBelow
  const fitsAbove = tooltipRect.height <= availableAbove
  const maxLeft = Math.max(POPOVER_MARGIN, viewportWidth - tooltipRect.width - POPOVER_MARGIN)
  const left = clamp(anchorRect.left + anchorRect.width / 2 - tooltipRect.width / 2, POPOVER_MARGIN, maxLeft)

  let top: number
  let placement = 'overlap'

  if (fitsBelow || fitsAbove) {
    placement = fitsBelow ? 'bottom' : 'top'
    top = placement === 'bottom' ? anchorRect.bottom + POPOVER_GAP : anchorRect.top - tooltipRect.height - POPOVER_GAP
  } else {
    const maxHeight = Math.max(160, viewportHeight - POPOVER_MARGIN * 2)
    if (tooltipRect.height > maxHeight) {
      tooltip.style.maxHeight = `${maxHeight}px`
      tooltip.style.overflowY = 'auto'
      tooltipRect = tooltip.getBoundingClientRect()
    }
    top = anchorRect.top + anchorRect.height / 2 - tooltipRect.height / 2
  }

  const maxTop = Math.max(POPOVER_MARGIN, viewportHeight - tooltipRect.height - POPOVER_MARGIN)
  tooltip.dataset.placement = placement
  tooltip.style.left = `${Math.round(left)}px`
  tooltip.style.top = `${Math.round(clamp(top, POPOVER_MARGIN, maxTop))}px`
  tooltip.style.visibility = 'visible'
}

function closePopover() {
  clearOpenTimer()
  if (!activePopover) {
    return
  }

  clearCloseTimer(activePopover)
  document.querySelectorAll<HTMLElement>('.w-tooltip[role="tooltip"]').forEach(tooltip => tooltip.remove())
  window.removeEventListener('resize', activePopover.update)
  window.removeEventListener('scroll', activePopover.update, true)
  document.removeEventListener('pointerdown', handleDocumentPointerDown, true)
  document.removeEventListener('keydown', handleDocumentKeyDown)
  activePopover.tooltip.remove()
  activePopover = null
}

function scheduleClose(popover: ActivePopover | null = activePopover) {
  if (!popover) {
    return
  }
  clearCloseTimer(popover)
  popover.closeTimer = window.setTimeout(() => {
    if (activePopover === popover) {
      closePopover()
    }
  }, CLOSE_DELAY)
}

function handleDocumentPointerDown(event: PointerEvent) {
  if (!activePopover || !(event.target instanceof Node)) {
    return
  }
  if (activePopover.anchor.contains(event.target) || activePopover.tooltip.contains(event.target)) {
    return
  }
  closePopover()
}

function handleDocumentKeyDown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    closePopover()
  }
}

function renderLoading(tooltip: HTMLElement) {
  tooltip.innerHTML = '<div class="profile-popover-loading">Загрузка профиля...</div>'
}

function renderError(tooltip: HTMLElement, message = 'Не удалось загрузить профиль.') {
  tooltip.innerHTML = `<div class="profile-popover-error">${message}</div>`
}

function updatePopoverHtml(popover: ActivePopover, html: string) {
  popover.tooltip.innerHTML = html
  bindPopoverContent(popover)
  makeCustomTooltips(popover.tooltip)
  bindUserPopovers(popover.tooltip)
  window.requestAnimationFrame(popover.update)
}

async function loadPopover(popover: ActivePopover) {
  const cached = htmlCache.get(popover.userId)
  if (cached) {
    updatePopoverHtml(popover, cached)
    return
  }

  renderLoading(popover.tooltip)
  popover.update()

  try {
    const response = await fetch(userPreviewUrl(popover.anchor), {
      credentials: 'same-origin',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
      },
    })
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    const html = await response.text()
    htmlCache.set(popover.userId, html)
    if (activePopover === popover) {
      updatePopoverHtml(popover, html)
    }
  } catch (error) {
    if (activePopover === popover) {
      renderError(popover.tooltip)
      popover.update()
    }
  }
}

function openPopover(anchor: HTMLElement) {
  const userId = anchor.dataset.userId
  if (!userId || userId === '-1') {
    return
  }

  if (activePopover?.anchor === anchor) {
    clearCloseTimer(activePopover)
    activePopover.update()
    return
  }

  closePopover()

  const tooltip = document.createElement('div')
  tooltip.className = 'w-tooltip w-user-popover'
  tooltip.role = 'dialog'
  tooltip.setAttribute('aria-label', 'Профиль пользователя')
  document.body.appendChild(tooltip)

  const popover: ActivePopover = {
    anchor,
    tooltip,
    userId,
    closeTimer: null,
    update: () => placeUserPopover(anchor, tooltip),
  }

  activePopover = popover

  tooltip.addEventListener('mouseenter', () => clearCloseTimer(popover))
  tooltip.addEventListener('mouseleave', () => scheduleClose(popover))
  tooltip.addEventListener('focusin', () => clearCloseTimer(popover))
  tooltip.addEventListener('focusout', () => scheduleClose(popover))

  window.addEventListener('resize', popover.update)
  window.addEventListener('scroll', popover.update, true)
  document.addEventListener('pointerdown', handleDocumentPointerDown, true)
  document.addEventListener('keydown', handleDocumentKeyDown)

  loadPopover(popover)
}

function scheduleOpen(anchor: HTMLElement) {
  clearOpenTimer()
  openTimer = window.setTimeout(() => openPopover(anchor), OPEN_DELAY)
}

function bindPopoverContent(popover: ActivePopover) {
  popover.tooltip.querySelectorAll<HTMLElement>('[data-user-popover-close]').forEach(button => {
    button.addEventListener('click', closePopover)
  })

  popover.tooltip.querySelectorAll<HTMLFormElement>('.profile-popover-action-form').forEach(form => {
    form.addEventListener('submit', event => {
      event.preventDefault()
      submitPopoverForm(popover, form, event as SubmitEvent)
    })
  })
}

async function submitPopoverForm(popover: ActivePopover, form: HTMLFormElement, event: SubmitEvent) {
  const submitter = event.submitter instanceof HTMLElement ? event.submitter : null
  const confirmation = submitter?.dataset.confirm
  if (confirmation && !window.confirm(confirmation)) {
    return
  }

  form.classList.add('is-loading')
  form.querySelectorAll<HTMLButtonElement>('button').forEach(button => {
    button.disabled = true
  })

  try {
    const actionUrl = form.getAttribute('action') || ''
    if (!actionUrl) {
      throw new Error('Неверный URL для действия.')
    }

    const response = await fetch(actionUrl, {
      method: 'POST',
      body: new FormData(form),
      credentials: 'same-origin',
      headers: {
        Accept: 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
      },
    })
    let data: ModerateResponse
    try {
      data = (await response.json()) as ModerateResponse
    } catch (error) {
      throw new Error(response.ok ? 'Некорректный ответ сервера.' : `Действие не выполнено (${response.status}).`)
    }
    if (!response.ok || !data.ok) {
      throw new Error(data.message || 'Действие не выполнено.')
    }
    if (data.preview) {
      htmlCache.set(popover.userId, data.preview)
      updatePopoverHtml(popover, data.preview)
    }
  } catch (error) {
    const errorNode = document.createElement('div')
    errorNode.className = 'profile-popover-error'
    errorNode.textContent = error instanceof Error ? error.message : 'Действие не выполнено.'
    popover.tooltip.appendChild(errorNode)
    popover.update()
  } finally {
    form.classList.remove('is-loading')
    form.querySelectorAll<HTMLButtonElement>('button').forEach(button => {
      button.disabled = false
    })
  }
}

function bindAnchor(anchor: HTMLElement) {
  if (anchor.dataset.userPreviewBound === 'true') {
    return
  }
  if (!anchor.dataset.userId || anchor.dataset.userId === '-1') {
    return
  }

  anchor.dataset.userPreviewBound = 'true'

  anchor.addEventListener('mouseenter', () => scheduleOpen(anchor))
  anchor.addEventListener('mouseleave', () => {
    clearOpenTimer()
    scheduleClose()
  })
  anchor.addEventListener('focusin', () => scheduleOpen(anchor))
  anchor.addEventListener('focusout', () => {
    clearOpenTimer()
    scheduleClose()
  })
  anchor.addEventListener(
    'click',
    event => {
      if (!isCoarsePointer()) {
        return
      }
      if (activePopover?.anchor === anchor) {
        return
      }
      event.preventDefault()
      openPopover(anchor)
    },
    true,
  )
}

export function bindUserPopovers(root: ParentNode = document.body) {
  const anchors: HTMLElement[] = []
  if (root instanceof HTMLElement && root.matches('.w-user-preview-trigger[data-user-id]')) {
    anchors.push(root)
  }
  root.querySelectorAll<HTMLElement>('.w-user-preview-trigger[data-user-id]').forEach(anchor => anchors.push(anchor))
  anchors.forEach(bindAnchor)
}
