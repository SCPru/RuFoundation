import { wFetch } from '../util/fetch-util'

export interface PreviewData {
  pageId: string
  title: string
  source: string
  pathParams?: { [key: string]: string }
}

export interface PreviewResponse {
  title: string
  content: string
}

export function makePreview(data: PreviewData) {
  return wFetch<PreviewResponse>(`/api/preview`, { method: 'POST', sendJson: true, body: data })
}
