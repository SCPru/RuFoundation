export interface UserData {
    type: 'system' | 'anonymous' | 'user' | 'wikidot'
    id?: number
    avatar?: string
    name: string
    username: string
    showAvatar: boolean
    editor?: boolean
    staff?: boolean
    admin?: boolean
    visualGroup?: string
    visualGroupIndex?: number
}