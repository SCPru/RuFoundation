import { fetchAllArticles, fetchArticle, fetchArticleBacklinks, fetchArticleLog, fetchArticleVersion, fetchArticleVotes } from '../api/articles'
import { fetchArticleFiles } from '../api/files'
import { fetchForumPost, fetchForumPostVersions, previewForumPost } from '../api/forum'
import { callModule, ModuleRequest } from '../api/modules'
import { makePreview } from '../api/preview'
import { fetchPageRating, fetchPageVotes } from '../api/rate'
import { fetchAllTags } from '../api/tags'
import { fetchAllUsers } from '../api/user'

function onApiMessage(e: MessageEvent) {
  if (!e.data.hasOwnProperty('type') || !e.data.hasOwnProperty('target') || !e.data.hasOwnProperty('callId') || e.data.type !== 'ApiCall') return

  const availableModules = ['listpages', 'listusers', 'countpages', 'interwiki']

  const callModuleWrapper = (module: string, method: string, data: Partial<ModuleRequest>) => {
    if (!availableModules.includes(module)) throw new Error(`Unexpected or restricted module name: ${module}`)
    return callModule({ ...data, module, method })
  }

  const availableApiCalls: Record<string, (...args: any[]) => any> = {
    fetchAllArticles, // [no args]
    fetchArticle, // pageId
    fetchArticleLog, // pageId, from?, to?
    fetchArticleVersion, // pageId, revNumber, pathParams?
    fetchArticleVotes, // pageId
    fetchArticleBacklinks, // pageId
    fetchArticleFiles, // pageId
    previewForumPost, // source
    fetchForumPost, // postId, atDate?
    fetchForumPostVersions, // postId
    makePreview, // data
    fetchPageRating, // pageId
    fetchPageVotes, // pageId
    fetchAllTags, // [no args]
    fetchAllUsers, // [no args]
    callModule: callModuleWrapper, // module, method, data?
  }

  if (!availableApiCalls.hasOwnProperty(e.data.target)) {
    console.error(`Unexpected ApiCall target: ${e.data.target}`)
    return
  }

  availableApiCalls[e.data.target](...e.data.args)
    .then((response: any) => {
      const data = {
        type: 'ApiResponse',
        target: e.data.target,
        callId: e.data.callId,
        response,
      }
      e.source.postMessage(data, {
        targetOrigin: '*',
      })
    })
    .catch((err: any) => {
      console.error('ApiCall error with target:', e.data.target, err)
    })
}

export function attachApiMessageListener() {
  window.addEventListener('message', onApiMessage, false)
}
