import * as React from 'react';
import { Component } from 'react';
import {UserData} from '../api/user'
import ForumPostEditor, {ForumPostPreview, ForumPostSubmission} from '../forum/forum-post-editor'
import UserView from '../util/user-view'
import formatDate from '../util/date-format'
import {createForumThread, ForumNewThreadRequest} from '../api/forum'


interface Props {
    type: 'new_thread' | 'new_post' | 'edit_thread' | 'edit_post'
    user: UserData
    categoryId?: number
    cancelUrl?: string
}

interface State {
    preview?: ForumPostPreview
}


class ForumPostEditorEntrypoint extends Component<Props, State> {
    constructor(props) {
        super(props);
        this.state = {

        };
    }

    onClose = async () => {
        const { cancelUrl } = this.props;
        window.location.href = cancelUrl || '/forum/start';
    }

    onSubmit = async (input: ForumPostSubmission) => {
        const { categoryId } = this.props;
        const request: ForumNewThreadRequest = {
            categoryId,
            name: input.name,
            description: input.description,
            source: input.source
        };
        const { url } = await createForumThread(request);
        window.location.href = url;
    }

    onPreview = (input: ForumPostPreview) => {
        this.setState({ preview: input })
    }

    render() {
        const { user } = this.props;
        const { preview } = this.state;
        const previewDate = new Date();
        return (
            <>
                { preview && (
                    <>
                        <h2>Предпросмотр:</h2>
                        <div className="forum-thread-box">
                            <div className="description-block well">
                                { preview.description && <div className="head">Краткое описание:</div> }
                                { preview.description }
                                <div className="statistics">
                                    Создатель: <UserView data={user} avatarHover />
                                    <br/>
                                    Дата: {formatDate(previewDate)}
                                </div>
                            </div>
                            <div id="thread-container" className="thread-container">
                                <div id="thread-container-posts">
                                    <div className="post-container">
                                        <div className="post">
                                            <div className="long">
                                                <div className="head">
                                                    <div className="title">
                                                        { preview.name }
                                                    </div>
                                                    <div className="info">
                                                        <UserView data={user} avatarHover />
                                                        {' '}
                                                        <span className="odate" style={{ display: 'inline' }}>{formatDate(previewDate)}</span>
                                                    </div>
                                                </div>
                                                <div className="content" dangerouslySetInnerHTML={{ __html: preview.content }} />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </>
                ) }
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


export default ForumPostEditorEntrypoint