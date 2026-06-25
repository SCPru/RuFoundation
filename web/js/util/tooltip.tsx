import React, { cloneElement, isValidElement, useEffect, useLayoutEffect, useRef, useState } from 'react'
import * as ReactDOM from 'react-dom'

type TooltipPlacement = 'top' | 'bottom'

const TOOLTIP_MARGIN = 8
const TOOLTIP_GAP = 7

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}

function assignRef<T>(ref: React.Ref<T> | undefined, value: T | null) {
  if (!ref) {
    return
  }
  if (typeof ref === 'function') {
    ref(value)
  } else {
    ;(ref as React.MutableRefObject<T | null>).current = value
  }
}

export function placeTooltip(anchor: HTMLElement, tooltip: HTMLElement, preferredPlacement: TooltipPlacement = 'bottom') {
  const viewportWidth = document.documentElement.clientWidth
  const viewportHeight = document.documentElement.clientHeight
  const anchorRect = anchor.getBoundingClientRect()

  tooltip.style.maxHeight = ''
  tooltip.style.overflowY = ''
  tooltip.style.visibility = 'hidden'
  tooltip.style.left = '0px'
  tooltip.style.top = '0px'

  let tooltipRect = tooltip.getBoundingClientRect()
  const availableBelow = viewportHeight - anchorRect.bottom - TOOLTIP_GAP - TOOLTIP_MARGIN
  const availableAbove = anchorRect.top - TOOLTIP_GAP - TOOLTIP_MARGIN
  const fitsBelow = tooltipRect.height <= availableBelow
  const fitsAbove = tooltipRect.height <= availableAbove
  let placement: TooltipPlacement = preferredPlacement

  if (preferredPlacement === 'bottom' && !fitsBelow && (fitsAbove || availableAbove > availableBelow)) {
    placement = 'top'
  } else if (preferredPlacement === 'top' && !fitsAbove && (fitsBelow || availableBelow >= availableAbove)) {
    placement = 'bottom'
  }

  const availableHeight = Math.max(48, placement === 'top' ? availableAbove : availableBelow)
  if (tooltipRect.height > availableHeight) {
    tooltip.style.maxHeight = `${availableHeight}px`
    tooltip.style.overflowY = 'auto'
    tooltipRect = tooltip.getBoundingClientRect()
  }

  const maxLeft = Math.max(TOOLTIP_MARGIN, viewportWidth - tooltipRect.width - TOOLTIP_MARGIN)
  const left = clamp(anchorRect.left + anchorRect.width / 2 - tooltipRect.width / 2, TOOLTIP_MARGIN, maxLeft)
  const rawTop = placement === 'top' ? anchorRect.top - tooltipRect.height - TOOLTIP_GAP : anchorRect.bottom + TOOLTIP_GAP
  const maxTop = Math.max(TOOLTIP_MARGIN, viewportHeight - tooltipRect.height - TOOLTIP_MARGIN)
  const top = clamp(rawTop, TOOLTIP_MARGIN, maxTop)

  tooltip.dataset.placement = placement
  tooltip.style.left = `${Math.round(left)}px`
  tooltip.style.top = `${Math.round(top)}px`
  tooltip.style.visibility = 'visible'
}

function isNaturallyFocusable(element: HTMLElement) {
  return /^(A|BUTTON|INPUT|SELECT|TEXTAREA)$/.test(element.tagName)
}

export function makeCustomTooltips(root: ParentNode = document.body) {
  const candidates: HTMLElement[] = []

  if (root instanceof HTMLElement && (root.matches('[data-tooltip], [title]') || root.hasAttribute('data-tooltip'))) {
    candidates.push(root)
  }
  root.querySelectorAll<HTMLElement>('[data-tooltip], [title]').forEach(element => candidates.push(element))

  candidates.forEach(element => {
    if (element.dataset.tooltipBound === 'true' || element.hasAttribute('data-tooltip-ignore')) {
      return
    }

    const text = element.dataset.tooltip || element.getAttribute('title') || ''
    if (!text.trim()) {
      return
    }

    element.dataset.tooltip = text
    element.dataset.tooltipBound = 'true'
    element.removeAttribute('title')
    if (!element.hasAttribute('aria-label')) {
      element.setAttribute('aria-label', text)
    }
    if (!isNaturallyFocusable(element) && !element.hasAttribute('tabindex')) {
      element.tabIndex = 0
    }

    let tooltip: HTMLElement | null = null
    let closeTimer: number | null = null

    const close = () => {
      if (closeTimer !== null) {
        window.clearTimeout(closeTimer)
        closeTimer = null
      }
      tooltip?.remove()
      tooltip = null
      window.removeEventListener('resize', update)
      window.removeEventListener('scroll', update, true)
    }

    const update = () => {
      if (tooltip) {
        placeTooltip(element, tooltip)
      }
    }

    const open = () => {
      if (tooltip) {
        update()
        return
      }
      tooltip = document.createElement('div')
      tooltip.className = 'w-tooltip'
      tooltip.role = 'tooltip'
      tooltip.textContent = element.dataset.tooltip || ''
      document.body.appendChild(tooltip)
      update()
      window.addEventListener('resize', update)
      window.addEventListener('scroll', update, true)
    }

    element.addEventListener('mouseenter', open)
    element.addEventListener('focus', open)
    element.addEventListener('mouseleave', close)
    element.addEventListener('blur', close)
    element.addEventListener(
      'touchstart',
      () => {
        open()
        if (closeTimer !== null) {
          window.clearTimeout(closeTimer)
        }
        closeTimer = window.setTimeout(close, 1800)
      },
      { passive: true },
    )
  })
}

interface TooltipProps {
  content: React.ReactNode
  children: React.ReactElement
  className?: string
  disabled?: boolean
  placement?: TooltipPlacement
}

const Tooltip: React.FC<TooltipProps> = ({ content, children, className = '', disabled, placement = 'bottom' }) => {
  const [open, setOpen] = useState(false)
  const triggerRef = useRef<HTMLElement | null>(null)
  const tooltipRef = useRef<HTMLDivElement | null>(null)
  const closeTimerRef = useRef<number | null>(null)
  const idRef = useRef(`w-tooltip-${Math.random().toString(36).slice(2)}`)

  const close = () => {
    if (closeTimerRef.current !== null) {
      window.clearTimeout(closeTimerRef.current)
      closeTimerRef.current = null
    }
    setOpen(false)
  }

  const show = () => {
    if (!disabled && content) {
      setOpen(true)
    }
  }

  useLayoutEffect(() => {
    if (!open || !triggerRef.current || !tooltipRef.current) {
      return
    }

    const update = () => {
      if (triggerRef.current && tooltipRef.current) {
        placeTooltip(triggerRef.current, tooltipRef.current, placement)
      }
    }

    update()
    window.addEventListener('resize', update)
    window.addEventListener('scroll', update, true)

    return () => {
      window.removeEventListener('resize', update)
      window.removeEventListener('scroll', update, true)
    }
  }, [open, placement, content])

  useEffect(() => {
    return () => {
      if (closeTimerRef.current !== null) {
        window.clearTimeout(closeTimerRef.current)
      }
    }
  }, [])

  if (disabled || !content || !isValidElement(children)) {
    return children
  }

  const child = children as React.ReactElement<any>
  const childRef = (child as any).ref as React.Ref<HTMLElement> | undefined
  const childProps = child.props as any
  const mergedChild = cloneElement(child, {
    ref: (node: HTMLElement | null) => {
      triggerRef.current = node
      assignRef(childRef, node)
    },
    'aria-describedby': open ? idRef.current : childProps['aria-describedby'],
    onBlur: (e: React.FocusEvent<HTMLElement>) => {
      childProps.onBlur?.(e)
      close()
    },
    onFocus: (e: React.FocusEvent<HTMLElement>) => {
      childProps.onFocus?.(e)
      show()
    },
    onKeyDown: (e: React.KeyboardEvent<HTMLElement>) => {
      childProps.onKeyDown?.(e)
      if (e.key === 'Escape') {
        close()
      }
    },
    onMouseEnter: (e: React.MouseEvent<HTMLElement>) => {
      childProps.onMouseEnter?.(e)
      show()
    },
    onMouseLeave: (e: React.MouseEvent<HTMLElement>) => {
      childProps.onMouseLeave?.(e)
      close()
    },
    onTouchStart: (e: React.TouchEvent<HTMLElement>) => {
      childProps.onTouchStart?.(e)
      show()
      if (closeTimerRef.current !== null) {
        window.clearTimeout(closeTimerRef.current)
      }
      closeTimerRef.current = window.setTimeout(close, 1800)
    },
  })

  return (
    <>
      {mergedChild}
      {open &&
        ReactDOM.createPortal(
          <div className={`w-tooltip ${className}`} id={idRef.current} ref={tooltipRef} role="tooltip">
            {content}
          </div>,
          document.body,
        )}
    </>
  )
}

export default Tooltip
