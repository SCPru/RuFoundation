import * as React from 'react';
import { Component } from 'react';
import {UserData} from '../api/user';
import ForumPostEditor, {ForumPostPreviewData, ForumPostSubmissionData} from '../forum/forum-post-editor';
import {createForumPost, ForumNewPostRequest} from '../api/forum'
import ForumPostPreview from '../forum/forum-post-preview';


interface Props {
    user: UserData
    threadId: number
    threadName: string
}


interface State {
    preview?: ForumPostPreviewData
    open: boolean
}


class ForumNewPost extends Component<Props, State> {
    constructor(props) {
        super(props);
        this.state = {
            open: false
        };
    }

    onOpen = (e) => {
        e.preventDefault();
        e.stopPropagation();
        const closeCurrent = (window as any)._closePostEditor;
        if (closeCurrent) {
            closeCurrent();
        }
        this.setState({ open: true, preview: undefined });
    };

    onClose = async () => {
        this.setState({ open: false });
    };

    onSubmit = async (input: ForumPostSubmissionData) => {
        const { threadId } = this.props;
        const request: ForumNewPostRequest = {
            threadId,
            name: input.name,
            source: input.source
        };
        const { url } = await createForumPost(request);
        window.onhashchange = () => {
            window.location.reload();
        };
        window.location.href = url;
    };

    onPreview = (input: ForumPostPreviewData) => {
        this.setState({ preview: input })
    };

    render() {
        const { user, threadName } = this.props;
        const { open, preview } = this.state;
        return (!open) ? (
            <div className="new-post">
                <a href="#" onClick={this.onOpen}>Новое сообщение</a>
            </div>
        ) : (
            <>
                { preview && <ForumPostPreview preview={preview} user={user} /> }
                <ForumPostEditor isNew
                                 onClose={this.onClose}
                                 onSubmit={this.onSubmit}
                                 onPreview={this.onPreview}
                                 initialTitle={'Re: '+threadName}
                />
            </>
        )
    }
}


export default ForumNewPost