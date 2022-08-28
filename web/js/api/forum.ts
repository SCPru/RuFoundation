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

export async function createForumThread(request: ForumNewThreadRequest) {
    return await callModule<ForumNewThreadResponse>({module: 'forumnewthread', method: 'submit', params: request});
}

// todo: make this use newpost instead (once we have newpost)
export async function previewForumPost(source: string) {
    return await callModule<ModuleRenderResponse>({module: 'forumnewthread', method: 'preview', params: {source}});
}