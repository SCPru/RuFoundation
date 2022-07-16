import {wFetch} from "../util/fetch-util";
import {UserData} from "./user";

export interface ArticleData {
    pageId: string
    title?: string
    source?: string
    tags?: Array<string>
    parent?: string
    locked?: boolean
}

export async function createArticle(data: ArticleData) {
    await wFetch(`/api/articles/new`, {method: 'POST', sendJson: true, body: data});
}

export function fetchArticle(id: string): Promise<ArticleData> {
    return wFetch<ArticleData>(`/api/articles/${id}`);
}

export async function updateArticle(id: string, data: ArticleData) {
    await wFetch(`/api/articles/${id}`, {method: 'PUT', sendJson: true, body: data});
}

export async function deleteArticle(id: string) {
    await wFetch(`/api/articles/${id}`, {method: 'DELETE', sendJson: true});
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

export async function fetchArticleLog(id: string, from: number = 0, to: number = from+25): Promise<ArticleLog> {
    return await wFetch<ArticleLog>(`/api/articles/${id}/log?from=${from}&to=${to}`)
}
