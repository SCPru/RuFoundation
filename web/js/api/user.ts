export interface UserData {
    type: 'system' | 'anonymous' | 'user'
    avatar?: string
    name: string
    username: string
    showAvatar: boolean
}