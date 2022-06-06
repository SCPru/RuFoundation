export interface UserData {
    type: 'system' | 'anonymous' | 'user'
    id?: number
    avatar?: string
    name: string
    username: string
    showAvatar: boolean
}