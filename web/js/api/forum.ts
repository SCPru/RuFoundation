import { wFetch } from '../util/fetch-util'
import { callModule, ModuleRenderResponse } from './modules'
import { UserData } from './user'

export interface ForumNewThreadRequest {
  categoryId: number
  name: string
  description: string
  source: string
}

export interface ForumNewThreadResponse {
  url: string
}

export interface ForumNewPostRequest {
  threadId: number
  replyTo?: number
  name: string
  source: string
}

export interface ForumNewPostResponse {
  url: string
}

export interface ForumFetchPostRequest {
  postId: number
  atDate?: string
}

export interface ForumFetchPostResponse {
  postId: number
  createdAt: string
  updatedAt: string
  name: string
  source: string
  content: string
  hasRevisions?: boolean
  lastRevisionDate?: string
  lastRevisionAuthor?: UserData
}

export interface ForumUpdatePostRequest {
  postId: number
  name: string
  source: string
}

export interface ForumDeletePostRequest {
  postId: number
}

export interface ForumPinPostRequest {
  postId: number
  isPinned: boolean
}

export interface ForumPinPostResponse {
  postId: number
  isPinned: boolean
}

export interface ForumFetchPostVersionsRequest {
  postId: number
}

export interface ForumPostVersion {
  createdAt: string
  author: UserData
}

export interface ForumFetchPostVersionsResponse {
  versions: Array<ForumPostVersion>
}

export interface ForumReaction {
  id: number
  name: string
  imageUrl: string
  isActive: boolean
}

export interface ForumPostReactionSummary {
  reaction: ForumReaction
  count: number
  me: boolean
  users: Array<UserData>
}

export interface ForumReactionLimits {
  maxPerUser: number
  maxPerPost: number
}

export interface ForumPostReactionState {
  availableReactions: Array<ForumReaction>
  limits: ForumReactionLimits
  reactions: Array<ForumPostReactionSummary>
  totalCount: number
  myCount: number
  canReact: boolean
  canRemoveOwnReactions: boolean
  canModerateReactions: boolean
  canUseInactiveReactions: boolean
}

export interface ForumPostReactionRequest {
  postId: number
  reactionId: number
  userId?: number
  allUsers?: boolean
}

export interface ForumUpdateThreadRequest {
  threadId: number
  name?: string
  description?: string
  isLocked?: boolean
  isPinned?: boolean
  categoryId?: number
}

export interface ForumUpdateThreadResponse {
  threadId: number
  name: string
  description: string
  isLocked: boolean
  isPinned: boolean
  categoryId: number
}

export interface ForumThreadExportArticle {
  uid: number
  pageId: string
  title: string
}

export interface ForumThreadExportCategory {
  id: number
  name: string
  section: {
    id: number
    name: string
  }
}

export interface ForumThreadExportPostVersion {
  createdAt: string
  author: UserData
}

export interface ForumThreadExportPost {
  id: number
  name: string
  createdAt: string
  updatedAt: string
  author: UserData
  replyTo: number | null
  isPinned: boolean
  source: string
  content: string
  version: ForumThreadExportPostVersion | null
  reactionState: ForumPostReactionState
  replies: Array<ForumThreadExportPost>
}

export interface ForumThreadExport {
  id: number
  name: string
  description: string
  createdAt: string
  updatedAt: string
  author: UserData
  isPinned: boolean
  isLocked: boolean
  article: ForumThreadExportArticle | null
  category: ForumThreadExportCategory | null
  postCount: number
  availableReactions: Array<ForumReaction>
  reactionLimits: ForumReactionLimits
  posts: Array<ForumThreadExportPost>
}

export async function fetchForumThread(threadId: number) {
  return await wFetch<ForumThreadExport>(`/api/forum/${threadId}`)
}

export async function createForumThread(request: ForumNewThreadRequest) {
  return await callModule<ForumNewThreadResponse>({ module: 'forumnewthread', method: 'submit', params: request })
}

export async function previewForumPost(source: string) {
  return await callModule<ModuleRenderResponse>({ module: 'forumnewpost', method: 'preview', params: { source } })
}

export async function createForumPost(request: ForumNewPostRequest) {
  return await callModule<ForumNewPostResponse>({ module: 'forumnewpost', method: 'submit', params: request })
}

export async function fetchForumPost(postId: number, atDate?: string) {
  const request: ForumFetchPostRequest = {
    postId,
    atDate,
  }
  return await callModule<ForumFetchPostResponse>({ module: 'forumpost', method: 'fetch', params: request })
}

export async function updateForumPost(request: ForumUpdatePostRequest) {
  return await callModule<ForumFetchPostResponse>({ module: 'forumpost', method: 'update', params: request })
}

export async function deleteForumPost(postId: number) {
  const request: ForumDeletePostRequest = {
    postId,
  }
  await callModule({ module: 'forumpost', method: 'delete', params: request })
}

export async function pinForumPost(postId: number, isPinned: boolean) {
  const request: ForumPinPostRequest = {
    postId,
    isPinned,
  }
  return await callModule<ForumPinPostResponse>({ module: 'forumpost', method: 'pin', params: request })
}

export async function fetchForumPostVersions(postId: number) {
  const request: ForumFetchPostVersionsRequest = {
    postId,
  }
  return await callModule<ForumFetchPostVersionsResponse>({ module: 'forumpost', method: 'fetchversions', params: request })
}

export async function fetchForumPostReactions(postId: number) {
  return await callModule<ForumPostReactionState>({ module: 'forumpost', method: 'reactions', params: { postId } })
}

export async function addForumPostReaction(postId: number, reactionId: number) {
  const request: ForumPostReactionRequest = {
    postId,
    reactionId,
  }
  return await callModule<ForumPostReactionState>({ module: 'forumpost', method: 'react', params: request })
}

export async function removeForumPostReaction(postId: number, reactionId: number, userId?: number) {
  const request: ForumPostReactionRequest = {
    postId,
    reactionId,
    userId,
  }
  return await callModule<ForumPostReactionState>({ module: 'forumpost', method: 'unreact', params: request })
}

export async function removeAllForumPostReactions(postId: number, reactionId: number) {
  const request: ForumPostReactionRequest = {
    postId,
    reactionId,
    allUsers: true,
  }
  return await callModule<ForumPostReactionState>({ module: 'forumpost', method: 'unreact', params: request })
}

export async function updateForumThread(request: ForumUpdateThreadRequest) {
  return await callModule<ForumUpdateThreadResponse>({ module: 'forumthread', method: 'update', params: request })
}
