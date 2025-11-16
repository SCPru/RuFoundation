import { wFetch } from '../util/fetch-util'

export interface UserData {
  type: 'system' | 'anonymous' | 'normal' | 'wikidot'
  id?: number
  avatar?: string
  name: string
  username: string
  showAvatar: boolean
  editor?: boolean
  staff?: boolean
  admin?: boolean
  roles?: string
}

export function fetchAllUsers(): Promise<UserData[]> {
  return wFetch<UserData[]>('/api/users')
}

export interface AdminSusUser {
  user: {
    id: number
    name: string
  }
  ip: string
}

export function fetchAdminSusUsers(): Promise<AdminSusUser[]> {
  return wFetch<AdminSusUser[]>('/api/admin/users/sus')
}
