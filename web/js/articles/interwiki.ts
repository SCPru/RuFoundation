import { callModule, ModuleRenderResponse } from '../api/modules'

interface InterwikiConfiguration {
  params: Record<string, any>
  content: string
  loading: string
  pageId?: string
}

async function load(configuration: InterwikiConfiguration, node: HTMLElement) {
  node.innerHTML = configuration.loading || ''

  const response = await callModule<ModuleRenderResponse>({
    module: 'interwiki',
    method: 'render_for_languages',
    pageId: configuration.pageId,
    params: {
      ...configuration.params,
      content: configuration.content,
    },
  })

  node.innerHTML = response.result
}

export function makeInterwiki(node: HTMLElement) {
  // hack: mark node as already processed because it was
  if ((node as any)._interwiki) {
    return
  }
  ;(node as any)._interwiki = true
  // end hack

  try {
    const configuration: InterwikiConfiguration = JSON.parse(node.dataset.interwikiConfiguration!)
    load(configuration, node)
  } catch (e: any) {
    return
  }
}
