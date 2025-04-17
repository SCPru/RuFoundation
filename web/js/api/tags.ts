import { callModule } from './modules'

export interface Category {
  id: number
  name: string
  description: string
  slug: string
}

export interface Tag {
  categoryId: number
  name: string
}

export interface FetchAllTagsResponse {
  categories: Array<Category>
  tags: Array<Tag>
}

export async function fetchAllTags() {
  return await callModule<FetchAllTagsResponse>({ module: 'tagcloud', method: 'list_tags' })
}
