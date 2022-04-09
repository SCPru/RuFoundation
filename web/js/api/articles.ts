import {wFetch} from "../util/fetch-util";

export interface ArticleData {
    pageId: string
    title?: string
    source?: string
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

export interface ArticleLogEntry {
    revNumber: number
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
