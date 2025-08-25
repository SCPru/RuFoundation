import { wFetch } from '../util/fetch-util'
import { ModuleRateVote, ModuleRateVotesResponse, RatingMode } from './rate'
import { UserData } from './user'

export interface ArticleData {
  pageId: string
  title?: string
  source?: string
  tags?: Array<string>
  parent?: string
  locked?: boolean
}

export interface ArticleUpdateRequest extends ArticleData {
  forcePageId?: boolean
}

export async function createArticle(data: ArticleData) {
  await wFetch(`/api/articles/new`, { method: 'POST', sendJson: true, body: data })
}

export interface FullArticleRating {
  value: number
  mode: RatingMode
  votes: Array<ModuleRateVote>
  popularity: number
}

export interface FullArticleData {
  uid: number
  pageId: string
  title: string
  canonicalUrl: string
  createdAt: string
  updatedAt: string
  createdBy: UserData
  updatedBy: UserData
  rating: FullArticleRating
  tags: string[]
}

export function fetchAllArticles(): Promise<FullArticleData[]> {
  return wFetch<FullArticleData[]>('/api/articles')
}

export function fetchArticle(pageId: string): Promise<ArticleData> {
  return wFetch<ArticleData>(`/api/articles/${pageId}`)
}

export async function updateArticle(pageId: string, data: ArticleUpdateRequest): Promise<ArticleData> {
  return wFetch<ArticleData>(`/api/articles/${pageId}`, { method: 'PUT', sendJson: true, body: data })
}

export async function deleteArticle(pageId: string) {
  await wFetch(`/api/articles/${pageId}`, { method: 'DELETE', sendJson: true })
}

export interface ArticleLogEntry {
  revNumber: number
  user: UserData
  comment: string
  createdAt: string
  type: string
  meta: Record<string, any>
}

export interface ArticleLog {
  count: number
  entries: Array<ArticleLogEntry>
}

export async function fetchArticleLog(pageId: string, from: number = 0, to: number = from + 25): Promise<ArticleLog> {
  return await wFetch<ArticleLog>(`/api/articles/${pageId}/log?from=${from}&to=${to}`)
}

export async function revertArticleRevision(pageId: string, revNumber: number): Promise<ArticleData> {
  return await wFetch(`/api/articles/${pageId}/log`, { method: 'PUT', sendJson: true, body: { revNumber: revNumber } })
}

export interface ArticleVersion {
  source: string
  rendered: string
}

export async function fetchArticleVersion(pageId: string, revNum: number, pathParams?: { [key: string]: string }): Promise<ArticleVersion> {
  return await wFetch<ArticleVersion>(`/api/articles/${pageId}/version?revNum=${revNum}&pathParams=${JSON.stringify(pathParams)}`)
}

export interface ArticleBacklink {
  id: string
  title: string
  exists: boolean
}

export interface ArticleBacklinks {
  children: Array<ArticleBacklink>
  includes: Array<ArticleBacklink>
  links: Array<ArticleBacklink>
}

export async function fetchArticleBacklinks(pageId: string): Promise<ArticleBacklinks> {
  return await wFetch<ArticleBacklinks>(`/api/articles/${pageId}/links`)
}

export async function fetchArticleVotes(pageId: string): Promise<ModuleRateVotesResponse> {
  return await wFetch<ModuleRateVotesResponse>(`/api/articles/${pageId}/votes`)
}

export async function deleteArticleVotes(pageId: string): Promise<ModuleRateVotesResponse> {
  return await wFetch<ModuleRateVotesResponse>(`/api/articles/${pageId}/votes`, { method: 'DELETE' })
}
