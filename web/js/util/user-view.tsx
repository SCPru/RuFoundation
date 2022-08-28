import * as React from 'react';
import { Component } from 'react';
import {UserData} from "../api/user";


export const ANON_AVATAR = "/-/static/images/anon_avatar.png";
export const DEFAULT_AVATAR = "/-/static/images/default_avatar.png";
export const WIKIDOT_AVATAR = "/-/static/images/wikidot_avatar.png";


interface Props {
    data: UserData
    avatarHover?: boolean
    hideAvatar?: boolean
}


class UserView extends Component<Props> {
    render() {
        const { data, avatarHover, hideAvatar } = this.props;
        if (data.type === 'system') {
            return <span className={`printuser ${avatarHover!==false?'avatarhover':''}`}><strong>system</strong></span>
        }
        if (data.type === 'anonymous') {
            return (
                <span className={`printuser ${avatarHover!==false?'avatarhover':''}`}>
                    {data.showAvatar&&!hideAvatar&&<span><img className="small" src={ANON_AVATAR} alt="Anonymous User" /></span>}
                    <span>Anonymous User</span>
                </span>
            )
        }

        let avatar = (data.type === 'wikidot') ? WIKIDOT_AVATAR : (data.avatar || DEFAULT_AVATAR);

        return (
            <span className={`printuser w-user ${avatarHover!==false?'avatarhover':''}`} data-user-name={data.username}>
                {data.showAvatar&&!hideAvatar&&<a href={`/-/users/${data.id}-${encodeURIComponent(data.username)}`}><img className="small" src={avatar} alt={data.name} /></a>}
                &nbsp;
                <a href={`/-/users/${data.id}-${encodeURIComponent(data.username)}`}>{data.name}</a>
            </span>
        )
    }
}


export default UserView