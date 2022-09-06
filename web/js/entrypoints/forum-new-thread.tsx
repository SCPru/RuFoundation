import * as React from 'react';
import { Component } from 'react';
import {UserData} from '../api/user';
import ForumPostEditor, {ForumPostPreviewData, ForumPostSubmissionData} from '../forum/forum-post-editor';
import {createForumThread, ForumNewThreadRequest} from '../api/forum';
import ForumPostPreview from '../forum/forum-post-preview';


interface Props {
    user: UserData
    categoryId?: number
    cancelUrl?: string
}


interface State {
    preview?: ForumPostPreviewData
}


class ForumNewThread extends Component<Props, State> {
    constructor(props) {
        super(props);
        this.state = {

        };
    }

    onClose = async () => {
        const { cancelUrl } = this.props;
        window.location.href = cancelUrl || '/forum/start';
    };

    onSubmit = async (input: ForumPostSubmissionData) => {
        const { categoryId } = this.props;
        const request: ForumNewThreadRequest = {
            categoryId,
            name: input.name,
            description: input.description,
            source: input.source
        };
        const { url } = await createForumThread(request);
        window.location.href = url;
    };

    onPreview = (input: ForumPostPreviewData) => {
        this.setState({ preview: input })
    };

    render() {
        const { user } = this.props;
        const { preview } = this.state;
        return (
            <>
                { preview && <ForumPostPreview preview={preview} user={user} /> }
                <ForumPostEditor isThread
                                 isNew
                                 onClose={this.onClose}
                                 onSubmit={this.onSubmit}
                                 onPreview={this.onPreview}
                />
            </>
        )
    }
}


export default ForumNewThread