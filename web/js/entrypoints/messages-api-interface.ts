import { fetchArticle, fetchArticleLog, fetchArticleVersion, fetchArticleVotes, fetchArticleBacklinks } from "../api/articles";
import { fetchArticleFiles } from "../api/files";
import { fetchForumPost, fetchForumPostVersions, previewForumPost } from "../api/forum";
import { callModule } from "../api/modules";
import { makePreview } from "../api/preview";
import { fetchPageRating, fetchPageVotes } from "../api/rate";
import { fetchAllTags } from "../api/tags";


function onApiMessage(e) {
    if (!e.data.hasOwnProperty("type") || 
        !e.data.hasOwnProperty("target") || 
        !e.data.hasOwnProperty("callId") ||
        !e.data.hasOwnProperty("payload") || 
         e.data.type !== "ApiCall")
        return;

    const avaliableApiCalls = {
        fetchArticle: [fetchArticle, ["pageId"]],
        fetchArticleLog: [fetchArticleLog, ["pageId", "from", "to"]],
        fetchArticleVersion: [fetchArticleVersion, ["pageId", "revNum", "pathParams"]],
        fetchArticleVotes: [fetchArticleVotes, ["pageId"]],
        fetchArticleBacklinks: [fetchArticleBacklinks, ["pageId"]],
        fetchArticleFiles: [fetchArticleFiles, ["pageId"]],
        previewForumPost: [previewForumPost, ["source"]],
        fetchForumPost: [fetchForumPost, ["postId", "atDate"]],
        fetchForumPostVersions: [fetchForumPostVersions, ["postId"]],
        makePreview: [makePreview, ["data"]],
        fetchPageRating: [fetchPageRating, ["pageId"]],
        fetchPageVotes: [fetchPageVotes, ["pageId"]],
        fetchAllTags: [fetchAllTags, []]
    }

    if (!avaliableApiCalls.hasOwnProperty(e.data.target)) {
        console.error(`Unexpected ApiCall target: ${e.data.target}`);
        return;
    }
    
    const [target, args] = avaliableApiCalls[e.data.target];

    let callParams = [];
    for (const i in args) {
        const arg = args[i]
        if (e.data.payload.hasOwnProperty(arg)) 
            callParams.push(e.data.payload[arg]);
        else
            break;
    }

    target(...callParams)
    .then(result => {
        const response = {
            type: "ApiResponse",
            target: e.data.target,
            callId: e.data.callId,
            response: result
        }
        e.source.postMessage(response, "*");
    })
    .catch(err  => {
        console.error("ApiCall error with target:", e.data.target, err);
    })    
}


function onModuleMessage(e) {
    if (!e.data.hasOwnProperty("type") || 
        !e.data.hasOwnProperty("callId") ||
        !e.data.hasOwnProperty("payload") || 
         e.data.type !== "ModuleCall")
        return;

    const avaliableModules = ["listpages", "listusers", "countpages", "interwiki"]

    if (!avaliableModules.includes(e.data.payload.module)) {
        console.error(`Unexpected or restricted module name: ${e.data.payload.module}`);
        return;
    }

    callModule(e.data.payload)
    .then(result => {
        const response = {
            type: "ModuleResponse",
            callId: e.data.callId,
            response: result
        }
        e.source.postMessage(response, "*");
    })
    .catch(err  => {
        console.error("ModuleCall error with target:", e.data.target, err);
    })    
}


export function attachApiMessageListener() {
    window.addEventListener("message", onApiMessage, false);
    window.addEventListener("message", onModuleMessage, false);
}