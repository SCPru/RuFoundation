import ReactDOM, { Root } from 'react-dom/client'

type ElementWithReactRoot = Element & { __root?: Root }

export function renderTo(container: ElementWithReactRoot, what: React.ReactNode) {
  const root = container.__root || ReactDOM.createRoot(container)
  container.__root = root
  root.render(what)
}

export function unmountFromRoot(container: ElementWithReactRoot) {
  if (container.__root) {
    container.__root.unmount()
  }
  delete container.__root
}
