import {wFetch} from "../util/fetch-util";


export interface Notification {
    id: number
    title: string
    message: string
    created_at: string
    referred_to: string
    is_viewed: boolean
}


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


export async function getNotifications(cursor: number, limit: number=10, unread: boolean=false, mark_viewed: boolean=false) {
    return await wFetch<NotificationsResponse>(`/api/notifications?cursor=${cursor}&limit=${limit}&unread=${unread}&mark_as_viewed=${mark_viewed}`);
}


export async function subscribeToNotifications(data: NotificationSubscriptionData) {
    return await wFetch<NotificationSubscriptionResponse>(`/api/notifications/subscribe`, {method: 'POST', sendJson: true, body: data});
}


export async function unsubscribeFromNotifications(data: NotificationSubscriptionData) {
    return await wFetch<NotificationSubscriptionResponse>(`/api/notifications/subscribe`, {method: 'DELETE', sendJson: true, body: data});
}