import { UserData } from '~api/user'
import { wFetch } from '../util/fetch-util'

interface NotificationEntity {
  id: number
  name: string
  url: string
}

interface BaseNotification {
  id: number
  created_at: string
  referred_to: string
  is_viewed: boolean
}

interface NotificationNewArticleRevision extends BaseNotification {
  type: 'new_article_revision'
  user: UserData
  article: {
    uid: number
    pageId: string
    title: string
  }
  rev_id: number
  rev_number: number
  rev_type: string
  rev_meta: Record<string, any>
  comment: string
}

interface NotificationNewThreadPost extends BaseNotification {
  type: 'new_thread_post'
  author: UserData
  section: NotificationEntity
  category: NotificationEntity
  thread: NotificationEntity
  post: NotificationEntity
  message: string
}

interface NotificationNewPostReply extends BaseNotification {
  type: 'new_post_reply'
  author: UserData
  section: NotificationEntity
  category: NotificationEntity
  thread: NotificationEntity
  post: NotificationEntity
  origin: NotificationEntity
  message: string
}

interface NotificationGeneric extends BaseNotification {
  type: 'generic'
  title: string
  message: string
}

export type Notification = NotificationNewPostReply | NotificationNewThreadPost | NotificationGeneric | NotificationNewArticleRevision

export interface NotificationsResponse {
  cursor: number
  notifications: Notification[]
}

export interface NotificationSubscriptionData {
  pageId?: string
  forumThreadId?: number
}

export interface NotificationSubscriptionResponse {
  status?: string
}

export async function getNotifications(cursor: number, limit: number = 10, unread: boolean = false, mark_viewed: boolean = false) {
  return await wFetch<NotificationsResponse>(`/api/notifications?cursor=${cursor}&limit=${limit}&unread=${unread}&mark_as_viewed=${mark_viewed}`)
}

export async function subscribeToNotifications(data: NotificationSubscriptionData) {
  return await wFetch<NotificationSubscriptionResponse>(`/api/notifications/subscribe`, { method: 'POST', sendJson: true, body: data })
}

export async function unsubscribeFromNotifications(data: NotificationSubscriptionData) {
  return await wFetch<NotificationSubscriptionResponse>(`/api/notifications/subscribe`, { method: 'DELETE', sendJson: true, body: data })
}
