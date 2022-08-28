import {callModule, ModuleRenderResponse} from "./modules"
import {UserData} from "./user";
import {ModuleRateVotesResponse, RatingMode} from './rate'

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
}

export interface ForumFetchPostResponse {
    postId: number
    name: string
    source: string
    content: string
}

export interface ForumUpdatePostRequest {
    postId: number
    name: string
    source: string
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

export async function fetchForumPost(postId: number) {
    const request: ForumFetchPostRequest = {
        postId
    }
    return await callModule<ForumFetchPostResponse>({module: 'forumpost', method: 'fetch', params: request});
}

export async function updateForumPost(request: ForumUpdatePostRequest) {
    return await callModule<ForumFetchPostResponse>({module: 'forumpost', method: 'update', params: request})
}