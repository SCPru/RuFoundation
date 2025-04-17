export function makeTabView(node: HTMLElement) {
  // hack: mark node as already processed because it was
  if ((node as any)._tabview) {
    return
  }
  ;(node as any)._tabview = true
  // end hack

  const headers: NodeListOf<HTMLElement> = node.querySelectorAll(':scope > .yui-nav > li')
  const tabs: NodeListOf<HTMLElement> = node.querySelectorAll(':scope > .yui-content > .w-tabview-tab')

  if (headers.length !== tabs.length) {
    // this is very wrong
    return
  }

  const switchTab = (index: number) => {
    for (let i = 0; i < tabs.length; i++) {
      if (index === i) {
        tabs[i].style.display = 'block'
        headers[i].classList.add('selected')
        headers[i].setAttribute('title', 'active')
      } else {
        tabs[i].style.display = 'none'
        headers[i].classList.remove('selected')
        headers[i].removeAttribute('title')
      }
    }
  }

  for (let i = 0; i < headers.length; i++) {
    const header = headers[i]
    header.addEventListener('click', () => switchTab(i))
  }
}
