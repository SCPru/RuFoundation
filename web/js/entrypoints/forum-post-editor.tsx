import * as React from 'react';
import { Component } from 'react';
import {UserData} from '../api/user'


interface Props {
    type: 'new_thread' | 'new_post' | 'edit_thread' | 'edit_post'
    user: UserData
    categoryId?: number
    cancelUrl?: string
}

interface State {

}


class ForumPostEditor extends Component<Props, State> {
    state = {
        isCreate: false,
        bodyRef: null
    };

    render() {
        return <>forum post editor</>
    }
}


export default ForumPostEditor