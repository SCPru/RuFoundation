import {callModule, ModuleRenderResponse} from "./modules"
import {UserData} from "./user";

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
}

export interface ForumUpdatePostRequest {
    postId: number
    name: string
    source: string
}

export interface ForumDeletePostRequest {
    postId: number
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

export async function createForumThread(request: ForumNewThreadRequest) {
    return await callModule<ForumNewThreadResponse>({module: 'forumnewthread', method: 'submit', params: request});
}

export async function previewForumPost(source: string) {
    return await callModule<ModuleRenderResponse>({module: 'forumnewpost', method: 'preview', params: {source}});
}

export async function createForumPost(request: ForumNewPostRequest) {
    return await callModule<ForumNewPostResponse>({module: 'forumnewpost', method: 'submit', params: request});
}

export async function fetchForumPost(postId: number, atDate?: string) {
    const request: ForumFetchPostRequest = {
        postId,
        atDate
    }
    return await callModule<ForumFetchPostResponse>({module: 'forumpost', method: 'fetch', params: request});
}

export async function updateForumPost(request: ForumUpdatePostRequest) {
    return await callModule<ForumFetchPostResponse>({module: 'forumpost', method: 'update', params: request})
}

export async function deleteForumPost(postId: number) {
    const request: ForumDeletePostRequest = {
        postId
    }
    await callModule({module: 'forumpost', method: 'delete', params: request});
}

export async function fetchForumPostVersions(postId: number) {
    const request: ForumFetchPostVersionsRequest = {
        postId
    }
    return await callModule<ForumFetchPostVersionsResponse>({module: 'forumpost', method: 'fetchversions', params: request});
}

export async function updateForumThread(request: ForumUpdateThreadRequest) {
    return await callModule<ForumUpdateThreadResponse>({module: 'forumthread', method: 'update', params: request});
}
