import { wFetch } from '../util/fetch-util'

export interface ModuleRequest {
  module: string
  pageId?: string
  method: string
  pathParams?: Record<string, any>
  params?: Record<string, any>
  content?: string
}

export interface ModuleRenderResponse {
  result: string
}

export async function callModule<T>(request: ModuleRequest) {
  return await wFetch<T>(`/api/modules`, { method: 'POST', sendJson: true, body: request })
}
