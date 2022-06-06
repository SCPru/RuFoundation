import * as React from 'react';
import { Component } from 'react';
import {UserData} from "../api/user";


interface Props {
    data: UserData
}


class UserView extends Component<Props> {
    render() {
        const { data } = this.props;
        if (data.type === 'system') {
            return <span className="printuser"><strong>system</strong></span>
        }
        if (data.type === 'anonymous') {
            return (
                <span className="printuser">
                    {data.showAvatar&&<span><img className="small" src="/static/images/anon_avatar.png" alt="Anonymous User" /></span>}
                    <span>Anonymous User</span>
                </span>
            )
        }
        return (
            <span className="printuser" data-user-name={data.username}>
                {data.showAvatar&&<a href={`/-/users/${encodeURIComponent(data.username)}`}><img className="small" src="/static/images/default_avatar.png" alt={data.name} /></a>}
                <a href={`/-/users/${encodeURIComponent(data.username)}`}>{data.name}</a>
            </span>
        )
    }
}


export default UserView