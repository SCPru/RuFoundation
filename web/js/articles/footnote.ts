export function makeFootnote(node: HTMLElement) {
  // hack: mark node as already processed because it was
  if ((node as any)._footnote) {
    return
  }
  ;(node as any)._footnote = true
  // end hack

  const el: HTMLElement = document.querySelector(node.getAttribute('href'))

  if (!el) {
    return
  }

  let footnoteContainer = document.getElementById('odialog-hovertips')
  if (!footnoteContainer) {
    footnoteContainer = document.createElement('div')
    footnoteContainer.setAttribute('id', 'odialog-hovertips')
    Object.assign(footnoteContainer.style, {
      position: 'absolute',
      zIndex: '100',
      top: '0',
      width: '100%',
    })
    document.body.appendChild(footnoteContainer)
  }

  let footnoteHovertip: HTMLElement = footnoteContainer.querySelector('.hovertip.w-footnote-hovertip')
  if (!footnoteHovertip) {
    footnoteHovertip = document.createElement('div')
    footnoteHovertip.setAttribute('class', 'hovertip w-footnote-hovertip')
    Object.assign(footnoteHovertip.style, {
      width: 'auto',
      backgroundColor: 'white',
      position: 'fixed',
      display: 'none',
    })
    footnoteHovertip.innerHTML =
      '<div class="content"><div class="footnote"><div class="f-heading"></div><div class="f-content"></div><div class="f-footer">(нажмите, чтобы перейти к сноскам)</div></div></div>'
    footnoteContainer.appendChild(footnoteHovertip)
  }

  const footnoteHeading: HTMLElement = footnoteHovertip.querySelector('.f-heading')
  const footnoteContent: HTMLElement = footnoteHovertip.querySelector('.f-content')

  const shouldBeHeading = `Сноска ${node.textContent.trim()}.`
  const shouldBeContent: HTMLElement = el.cloneNode(true) as HTMLElement

  // drop the initial link and dot from shouldBeContent
  const linkToRemove = shouldBeContent.querySelector('a')
  linkToRemove.parentNode.removeChild(linkToRemove)

  // find first text node with the dot and remove the dot
  const textNodeToProcess = document.createNodeIterator(shouldBeContent, NodeFilter.SHOW_TEXT).nextNode()
  if (textNodeToProcess) {
    textNodeToProcess.nodeValue = textNodeToProcess.nodeValue.substring(2)
  }

  const enableAndPosition = (x, y) => {
    footnoteHovertip.style.display = 'block'
    footnoteHeading.textContent = shouldBeHeading
    footnoteContent.innerHTML = shouldBeContent.innerHTML
    position(x, y)
  }

  const position = (x, y) => {
    // add explicit max width
    const maxWidth = document.getElementById('content-wrap').getBoundingClientRect().width

    footnoteHovertip.style.maxWidth = `min(100vw, ${maxWidth}px)`
    footnoteHovertip.style.left = '0'
    footnoteHovertip.style.top = '0'
    const r = footnoteHovertip.getBoundingClientRect()
    const centeredX = x - r.width / 2 + 4
    if (centeredX + r.width > window.innerWidth) {
      x = Math.max(0, window.innerWidth - r.width)
    } else if (centeredX < 0) {
      x = 0
    } else {
      x = centeredX
    }
    if (y + r.height + 8 > window.innerHeight && y - 8 > r.height) {
      y = Math.max(0, y - r.height - 8)
    } else {
      y += 8
    }
    footnoteHovertip.style.left = `${x}px`
    footnoteHovertip.style.top = `${y}px`
  }

  const disable = () => {
    footnoteHovertip.style.display = 'none'
    footnoteHeading.textContent = ''
    footnoteContent.innerHTML = ''
  }

  node.addEventListener('mouseover', e => {
    enableAndPosition(e.clientX, e.clientY)
  })

  node.addEventListener('mouseout', () => {
    disable()
  })

  node.addEventListener('mousemove', e => {
    position(e.clientX, e.clientY)
  })
}
