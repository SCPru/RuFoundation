import { callModule } from './modules'
import { UserData } from './user'

export type RatingMode = 'disabled' | 'updown' | 'stars'

export interface ModuleRateResponse {
  pageId: string
  rating: number
  voteCount: number

  popularity: number
  mode: RatingMode
}

export interface ModuleRateVote {
  user: UserData
  value: number
  date?: string
  group?: string
  groupIndex?: number
}

export interface ModuleRateVotesResponse {
  pageId: string
  rating: number
  mode: RatingMode
  votes: Array<ModuleRateVote>
  popularity: number
}

export interface ModuleRateRequest {
  pageId: string
  value: number
}

export async function ratePage({ pageId, value }: ModuleRateRequest): Promise<ModuleRateResponse> {
  return await callModule<ModuleRateResponse>({ module: 'rate', method: 'rate', pageId, params: { value } })
}

export async function fetchPageRating(pageId: string) {
  return await callModule<ModuleRateResponse>({ module: 'rate', method: 'get_rating', pageId })
}

export async function fetchPageVotes(pageId: string) {
  return await callModule<ModuleRateVotesResponse>({ module: 'rate', method: 'get_votes', pageId })
}
