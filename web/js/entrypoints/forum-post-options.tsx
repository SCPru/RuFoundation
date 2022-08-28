import * as React from 'react';
import { Component } from 'react';
import {UserData} from '../api/user';
import ForumPostEditor, {ForumPostPreviewData, ForumPostSubmissionData} from '../forum/forum-post-editor';
import {createForumPost, ForumNewPostRequest, ForumUpdatePostRequest, updateForumPost} from '../api/forum'
import ForumPostPreview from '../forum/forum-post-preview';


interface Props {
    user: UserData
    threadId: number
    threadName: string
    postId: number
    postName: string
    canReply?: boolean
    canEdit?: boolean
    canDelete?: boolean
}


interface State {
    isEditing: boolean
    isReplying: boolean
    replyPreview?: ForumPostPreviewData
    open: boolean
    originalPreviewTitle?: string
    originalPreviewContent?: string
}


class ForumPostOptions extends Component<Props, State> {
    refSelf: HTMLElement = null;
    refPreviewTitle: HTMLElement = null;
    refPreviewContent: HTMLElement = null;

    constructor(props) {
        super(props);
        this.state = {
            isEditing: false,
            isReplying: false,
            open: false
        };
    }

    componentDidMount() {
        if (!this.refSelf) {
            // something bad happened
            return
        }
        const longPost = this.refSelf.parentNode.parentNode;
        this.refPreviewTitle = longPost.querySelector('.head .title');
        this.refPreviewContent = longPost.querySelector('.content');
        this.setState({ originalPreviewTitle: this.refPreviewTitle.textContent, originalPreviewContent: this.refPreviewContent.innerHTML });
    }

    onReplyClose = () => {
        this.setState({ isReplying: false });
    };

    onReplySubmit = async (input: ForumPostSubmissionData) => {
        const { threadId, postId } = this.props;
        const request: ForumNewPostRequest = {
            threadId,
            replyTo: postId,
            name: input.name,
            source: input.source
        };
        const { url } = await createForumPost(request);
        this.onReplyClose();
        window.onhashchange = () => {
            window.location.reload();
        };
        window.location.href = url;
    };

    onReplyPreview = (input: ForumPostPreviewData) => {
        this.setState({ replyPreview: input });
    };

    onReply = (e) => {
        e.preventDefault();
        e.stopPropagation();
        const closeCurrent = (window as any)._closePostEditor;
        if (closeCurrent) {
            closeCurrent();
        }
        this.setState({ isReplying: true });
    };

    onEditClose = () => {
        const { originalPreviewTitle, originalPreviewContent } = this.state;
        this.refPreviewTitle.textContent = originalPreviewTitle;
        this.refPreviewContent.innerHTML = originalPreviewContent;
        this.setState({ isEditing: false });
    };

    onEditSubmit = async (input: ForumPostSubmissionData) => {
        const { postId } = this.props;
        const request: ForumUpdatePostRequest = {
            postId,
            name: input.name,
            source: input.source
        };
        const result = await updateForumPost(request);
        this.refPreviewTitle.textContent = result.name;
        this.refPreviewContent.innerHTML = result.content;
        this.setState({ originalPreviewTitle: result.name, originalPreviewContent: result.content });
        this.onEditClose();
    };

    onEditPreview = (input: ForumPostPreviewData) => {
        this.refPreviewTitle.textContent = input.name;
        this.refPreviewContent.innerHTML = input.content;
    };

    onEdit = (e) => {
        e.preventDefault();
        e.stopPropagation();
        const closeCurrent = (window as any)._closePostEditor;
        if (closeCurrent) {
            closeCurrent();
        }
        this.setState({ isEditing: true });
    };

    onDelete = (e) => {

    };

    onToggle = () => {
        const { open } = this.state;
        this.setState({ open: !open });
    };

    render() {
        const { canReply, canEdit, canDelete, user, threadName, postName, postId } = this.props;
        const { open, isReplying, isEditing, replyPreview } = this.state;
        return (
            <>
                <div style={{ display: 'none' }} ref={r=>this.refSelf=r} />
                {canReply && <strong><a href="javascript:;" onClick={this.onReply}>Ответить</a></strong>}
                {' '}
                {canEdit && canDelete && <a href="javascript:;" onClick={this.onToggle}>Опции</a>}
                {open && (
                    <div className="options">
                        {canEdit && <a href="javascript:;" onClick={this.onEdit}>Редактировать</a>}
                        {' '}
                        {canDelete && <a href="javascript:;" onClick={this.onDelete}>Удалить</a>}
                    </div>
                )}
                {isReplying && (
                    <div className="post-container">
                        {replyPreview && (
                            <ForumPostPreview preview={replyPreview} user={user} />
                        )}
                        <ForumPostEditor isNew
                                         onClose={this.onReplyClose}
                                         onSubmit={this.onReplySubmit}
                                         onPreview={this.onReplyPreview}
                                         initialTitle={'Re: '+(postName || threadName)}
                        />
                    </div>
                )}
                {isEditing && (
                    <ForumPostEditor postId={postId}
                                     onClose={this.onEditClose}
                                     onSubmit={this.onEditSubmit}
                                     onPreview={this.onEditPreview}
                    />
                )}
            </>
        )
    }
}


export default ForumPostOptions