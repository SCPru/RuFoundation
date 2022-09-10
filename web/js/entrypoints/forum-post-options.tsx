import * as React from 'react';
import { Component } from 'react';
import * as ReactDOM from 'react-dom';
import {UserData} from '../api/user';
import ForumPostEditor, {ForumPostPreviewData, ForumPostSubmissionData} from '../forum/forum-post-editor';
import {
    createForumPost,
    deleteForumPost, fetchForumPost, fetchForumPostVersions,
    ForumNewPostRequest, ForumPostVersion,
    ForumUpdatePostRequest,
    updateForumPost
} from '../api/forum'
import ForumPostPreview from '../forum/forum-post-preview';
import WikidotModal from '../util/wikidot-modal'
import formatDate from '../util/date-format'
import UserView from '../util/user-view'


interface Props {
    user: UserData
    threadId: number
    threadName: string
    postId: number
    postName: string
    canReply?: boolean
    canEdit?: boolean
    canDelete?: boolean
    hasRevisions?: boolean
    lastRevisionDate?: string
    lastRevisionAuthor?: UserData
}


interface State {
    isEditing: boolean
    isReplying: boolean
    open: boolean
    originalPreviewTitle?: string
    originalPreviewContent?: string
    deleteError?: string
    revisionsOpen: boolean
    hasRevisions?: boolean
    lastRevisionDate?: string
    lastRevisionAuthor?: UserData
    currentRevision?: string
    revisions?: Array<ForumPostVersion>
}


class ForumPostOptions extends Component<Props, State> {
    refSelf: HTMLElement = null;
    refPreviewTitle: HTMLElement = null;
    refPreviewContent: HTMLElement = null;
    refReplyPreview: HTMLElement = null;

    constructor(props: Props) {
        super(props);
        this.state = {
            isEditing: false,
            isReplying: false,
            open: false,
            revisionsOpen: false,
            currentRevision: undefined,
            hasRevisions: props.hasRevisions,
            lastRevisionDate: props.lastRevisionDate,
            lastRevisionAuthor: props.lastRevisionAuthor
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
        let refReplyPreview: HTMLElement = longPost.querySelector('.w-reply-preview');
        if (!refReplyPreview) {
            refReplyPreview = document.createElement('div');
            refReplyPreview.className = 'w-reply-preview';
            this.refSelf.parentNode.insertBefore(refReplyPreview, this.refSelf);
        }
        this.refReplyPreview = refReplyPreview;
        this.setState({ originalPreviewTitle: this.refPreviewTitle.textContent, originalPreviewContent: this.refPreviewContent.innerHTML });
    }

    onReplyClose = () => {
        this.setState({ isReplying: false });
        if (this.refReplyPreview.firstChild) {
            ReactDOM.unmountComponentAtNode(this.refReplyPreview);
            this.refReplyPreview.innerHTML = '';
        }
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
        const { user } = this.props;
        ReactDOM.render(<ForumPostPreview preview={input} user={user}/>, this.refReplyPreview);
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
        this.setState({ revisionsOpen: false, currentRevision: undefined });
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

    onOpenRevisions = async (e) => {
        e.preventDefault();
        e.stopPropagation();
        try {
            const {postId} = this.props;
            const revisions = await fetchForumPostVersions(postId);
            this.setState({ revisionsOpen: true, revisions: revisions.versions });
        } catch (e) {
            this.setState({ revisionsOpen: false, deleteError: e.error || 'Ошибка связи с сервером' });
        }

    }

    onCloseRevisions = (e) => {
        e.preventDefault();
        e.stopPropagation();
        const { originalPreviewTitle, originalPreviewContent, currentRevision } = this.state;
        if (currentRevision) {
            this.refPreviewTitle.textContent = originalPreviewTitle;
            this.refPreviewContent.innerHTML = originalPreviewContent;
        }
        this.setState({ revisionsOpen: false, currentRevision: undefined });
    }

    onShowRevision = async (e, date) => {
        e.preventDefault();
        e.stopPropagation();
        const { postId } = this.props;
        const data = await fetchForumPost(postId, date);
        this.setState({ currentRevision: date });
        this.refPreviewTitle.textContent = data.name;
        this.refPreviewContent.innerHTML = data.content;
    }

    render() {
        const { canReply, canEdit, canDelete, threadName, postName, postId } = this.props;
        const {
            open, isReplying, isEditing, deleteError,
            lastRevisionAuthor, lastRevisionDate, hasRevisions, revisionsOpen, revisions, currentRevision
        } = this.state;

        return (
            <>
                {(hasRevisions && lastRevisionDate && lastRevisionAuthor && !revisionsOpen) && (
                    <div className="changes" style={{ display: 'block' }}>
                        Последнее редактирование <span className="odate" style={{ display: 'inline' }}>{formatDate(new Date(lastRevisionDate))}</span>
                        {' '}от <UserView data={lastRevisionAuthor} hideAvatar />
                        {' '}<a href="#" onClick={this.onOpenRevisions}><i className="icon-plus" /> Показать ещё</a>
                    </div>
                )}
                {revisionsOpen && (
                    <div className="revisions" style={{ display: 'block' }}>
                        <a href="#" onClick={this.onCloseRevisions}>- Скрыть</a>
                        <div className="title">Версии сообщения</div>
                        <table className="table">
                        <tbody>
                        {(revisions||[]).map((rev, i) => (
                            <tr className={(currentRevision===rev.createdAt||(i===0&&!currentRevision))?'active':''} key={i}>
                                <td><UserView data={rev.author} hideAvatar /></td>
                                <td>{formatDate(new Date(rev.createdAt))}</td>
                                <td><a href="#" onClick={(e) => this.onShowRevision(e, rev.createdAt)}>Показать правки</a></td>
                            </tr>
                        ))}
                        </tbody>
                        </table>
                    </div>
                )}
                <div style={{ display: 'none' }} ref={r=>this.refSelf=r?.parentElement} />
                { deleteError && (
                    <WikidotModal buttons={[{title: 'Закрыть', onClick: this.onCloseError}]}>
                        <strong>Ошибка:</strong> {deleteError}
                    </WikidotModal>
                ) }
                {canReply && <strong><a href="#" onClick={this.onReply}>Ответить</a></strong>}
                {' '}
                {(canEdit || canDelete) && <a href="#" onClick={this.onToggle}>Опции</a>}
                {open && (
                    <div className="options">
                        {canEdit && <a href="#" onClick={this.onEdit}>Редактировать</a>}
                        {' '}
                        {canDelete && <a href="#" onClick={this.onDelete}>Удалить</a>}
                    </div>
                )}
                {isReplying && (
                    <div className="post-container">
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