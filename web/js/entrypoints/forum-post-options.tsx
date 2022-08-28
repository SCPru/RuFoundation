import * as React from 'react';
import { Component } from 'react';
import * as ReactDOM from 'react-dom';
import {UserData} from '../api/user';
import ForumPostEditor, {ForumPostPreviewData, ForumPostSubmissionData} from '../forum/forum-post-editor';
import {
    createForumPost,
    deleteForumPost,
    ForumNewPostRequest,
    ForumUpdatePostRequest,
    updateForumPost
} from '../api/forum'
import ForumPostPreview from '../forum/forum-post-preview';
import WikidotModal from '../util/wikidot-modal'


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
    originalPreviewContent?: string,
    deleteError?: string
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
        const longPost = this.refSelf.parentNode;
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

    onDelete = async (e) => {
        e.preventDefault();
        e.stopPropagation();
        const { postId } = this.props;
        try {
            await deleteForumPost(postId);
        } catch (e) {
            this.setState({ deleteError: e.error || 'Ошибка связи с сервером' })
            return
        }
        // successful deletion. reflect the changes (drop the current post / tree)
        // first, unmount self. this makes sure any editors are taken care of
        const post = this.refSelf.parentElement.parentElement; // should point to class .post
        ReactDOM.unmountComponentAtNode(this.refSelf);
        const parent = post.parentElement;
        parent.removeChild(post);
        if (parent.classList.contains('post-container') && parent.parentElement.classList.contains('post-container')) {
            // check if parent element has no children anymore
            if (!parent.firstElementChild) {
                parent.parentNode.removeChild(parent);
            }
        }
    };

    onToggle = (e) => {
        e.preventDefault();
        e.stopPropagation();
        const { open } = this.state;
        this.setState({ open: !open });
    };

    onCloseError = () => {
        this.setState({deleteError: undefined});
    };

    render() {
        const { canReply, canEdit, canDelete, user, threadName, postName, postId } = this.props;
        const { open, isReplying, isEditing, replyPreview, deleteError } = this.state;
        return (
            <>
                <div style={{ display: 'none' }} ref={r=>this.refSelf=r?.parentElement} />
                { deleteError && (
                    <WikidotModal buttons={[{title: 'Закрыть', onClick: this.onCloseError}]}>
                        <strong>Ошибка:</strong> {deleteError}
                    </WikidotModal>
                ) }
                {canReply && <strong><a href="#" onClick={this.onReply}>Ответить</a></strong>}
                {' '}
                {canEdit && canDelete && <a href="#" onClick={this.onToggle}>Опции</a>}
                {open && (
                    <div className="options">
                        {canEdit && <a href="#" onClick={this.onEdit}>Редактировать</a>}
                        {' '}
                        {canDelete && <a href="#" onClick={this.onDelete}>Удалить</a>}
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