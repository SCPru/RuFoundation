import { wFetch, WRequestUploadProgressHandler } from '../util/fetch-util'
import { UserData } from './user'

export interface ArticleFile {
  id: number
  name: string
  createdAt: string
  author: UserData
  mimeType: string
  size: number
}

export interface ArticleFiles {
  pageId: string
  files: Array<ArticleFile>
  softLimit: number
  hardLimit: number
  softUsed: number
  hardUsed: number
}

export async function fetchArticleFiles(pageId: string): Promise<ArticleFiles> {
  return await wFetch<ArticleFiles>(`/api/articles/${pageId}/files`)
}

export async function uploadFile(pageId: string, file: File, fileName: string, uploadProgressHandler?: WRequestUploadProgressHandler) {
  return await wFetch(`/api/articles/${pageId}/files`, {
    method: 'POST',
    backend: 'xhr',
    uploadProgressHandler,
    body: file,
    headers: {
      'X-File-Name': fileName,
    },
  })
}

export async function renameFile(fileId: number, newFileName: string) {
  return await wFetch(`/api/files/${encodeURIComponent(fileId)}`, {
    method: 'PUT',
    sendJson: true,
    body: { name: newFileName },
  })
}

export async function deleteFile(fileId: number) {
  return await wFetch(`/api/files/${encodeURIComponent(fileId)}`, {
    method: 'DELETE',
  })
}
