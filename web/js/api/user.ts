export interface UserData {
    type: 'system' | 'anonymous' | 'user' | 'wikidot'
    id?: number
    avatar?: string
    name: string
    username: string
    showAvatar: boolean
    staff?: boolean
    admin?: boolean
}