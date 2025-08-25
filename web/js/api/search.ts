import { FullArticleData } from '~api/articles'
import { wFetch } from '~util/fetch-util'

interface SearchParams {
  mode?: 'source' | 'plain'
  limit?: number
  cursor?: string
}

interface SearchArticleData extends FullArticleData {
  words: Array<string>
  excerpts: Array<string>
}

export interface SearchResults {
  results: Array<SearchArticleData>
  cursor: string
}

export function fetchSearch(text: string, opts?: SearchParams): Promise<SearchResults> {
  const params = new URLSearchParams()

  params.set('text', text)
  params.set('limit', `${opts?.limit ?? 25}`)
  params.set('mode', opts?.mode ?? 'plain')

  if (opts?.cursor) {
    params.set('cursor', opts.cursor)
  }

  return wFetch<SearchResults>(`/api/search?${params.toString()}`)
}
