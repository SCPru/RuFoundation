import * as React from 'react';
import { Component } from 'react';
import {updateForumThread} from '../api/forum'
import WikidotModal from '../util/wikidot-modal'

interface CategoryInfo {
    name: string
    id: number
    canMove: boolean
}

interface Props {
    threadId: number
    threadName: string
    threadDescription: string
    canEdit: boolean
    canPin: boolean
    canMove: boolean
    canLock: boolean
    isLocked: boolean
    isPinned: boolean
    categoryId: number
    moveTo: Array<CategoryInfo>
}


interface State {
    isLoading: boolean
    error?: string
    isEditing: boolean
    isMoving: boolean
    editName?: string
    editDescription?: string
    moveCategoryId?: number
}


class ForumThreadOptions extends Component<Props, State> {
    constructor(props) {
        super(props)
        this.state = {
            isLoading: false,
            isEditing: false,
            isMoving: false
        };
    }

    componentDidMount() {
    }

    onEdit = async (e) => {
        e.preventDefault();
        e.stopPropagation();

        const { threadName, threadDescription } = this.props;

        this.setState({ isEditing: true, editName: threadName, editDescription: threadDescription });
    };

    onPin = async (e) => {
        e.preventDefault();
        e.stopPropagation();

        const { threadId, isPinned } = this.props;

        this.setState({ isLoading: true, error: null });

        try {
            await updateForumThread({
                threadId, isPinned: !isPinned
            });
        } catch (e) {
            this.setState({ error: e.error || 'Ошибка связи с сервером' });
            this.setState({ isLoading: false });
            return;
        }

        this.setState({ isLoading: false });
        window.location.reload();
    };

    onLock = async (e) => {
        e.preventDefault();
        e.stopPropagation();

        const { threadId, isLocked } = this.props;

        this.setState({ isLoading: true, error: null });

        try {
            await updateForumThread({
                threadId, isLocked: !isLocked
            });
        } catch (e) {
            this.setState({ error: e.error || 'Ошибка связи с сервером' });
            this.setState({ isLoading: false });
            return;
        }

        this.setState({ isLoading: false });
        window.location.reload();
    };

    onMove = async (e) => {
        e.preventDefault();
        e.stopPropagation();

        const { categoryId } = this.props;

        this.setState({ isMoving: true, moveCategoryId: categoryId });
    };

    onCloseError = () => {
        this.setState({ error: null });
    };

    onEditCancel = () => {
        this.setState({ isEditing: false });
    };

    onEditSave = async () => {
        const { threadId } = this.props;
        const { editName, editDescription } = this.state;

        this.setState({ isLoading: true });

        try {
            await updateForumThread({
                threadId, name: editName, description: editDescription
            })
        } catch (e) {
            this.setState({error: e.error || 'Ошибка связи с сервером'})
            this.setState({ isLoading: false });
            return;
        }

        this.setState({ isLoading: false });
        window.location.reload();
    };

    onChange(k: keyof State, v) {
        this.setState({ [k]: v } as unknown)
    }

    renderEdit() {
        const { editName, editDescription } = this.state;

        return (
            <WikidotModal buttons={[{title: 'Отмена', onClick: this.onEditCancel}, {title: 'Сохранить', onClick: this.onEditSave}]}>
                <h2>Редактировать название и описание темы</h2>
                <hr className="buttons-hr" />
                <table className="form">
                <tbody>
                <tr>
                    <td>Заголовок темы:</td>
                    <td>
                        <input className="text form-control" type="text" value={editName} size={50} maxLength={99} onChange={e=>this.onChange('editName', e.target.value)} />
                    </td>
                </tr>
                <tr>
                    <td>Описание:</td>
                    <td>
                        <textarea cols={50} rows={2} className="form-control" value={editDescription} onChange={e=>this.onChange('editDescription', e.target.value)} />
                    </td>
                </tr>
                </tbody>
                </table>
            </WikidotModal>
        )
    }

    onMoveSave = async () => {
        const { threadId } = this.props;
        const { moveCategoryId } = this.state;

        this.setState({ isLoading: true });

        try {
            await updateForumThread({
                threadId, categoryId: moveCategoryId
            })
        } catch (e) {
            this.setState({error: e.error || 'Ошибка связи с сервером'})
            this.setState({ isLoading: false });
            return;
        }

        this.setState({ isLoading: false });
        window.location.reload();
    };

    onMoveCancel = () => {
        this.setState({ isMoving: false });
    };

    renderMove() {
        const { moveTo, categoryId } = this.props;
        const { moveCategoryId } = this.state;

        return (
            <WikidotModal buttons={[{title: 'Отмена', onClick: this.onMoveCancel}, {title: 'Сохранить', onClick: this.onMoveSave}]}>
                <h2>Переместить тему</h2>
                <hr className="buttons-hr" />
                <table className="form">
                    <tbody>
                    <tr>
                        <td>Укажите новый раздел:</td>
                        <td>
                            <select className="form-control" value={moveCategoryId} onChange={e => this.onChange('moveCategoryId', Number.parseInt(e.target.value))}>
                                {moveTo.map(c => (
                                    <option key={c.id} disabled={!c.canMove || c.id === categoryId} value={c.id}>{c.name}</option>
                                ))}
                            </select>
                        </td>
                    </tr>
                    </tbody>
                </table>
            </WikidotModal>
        )
    }

    render() {
        const { canEdit, canMove, canLock, canPin, isLocked, isPinned } = this.props;

        if (!canEdit && !canMove && !canLock && !canPin) {
            return null;
        }

        const { isLoading, error, isEditing, isMoving } = this.state;

        return (
            <>
                {isEditing && this.renderEdit()}
                {isMoving && this.renderMove()}
                {isLoading && <WikidotModal isLoading><p>Сохранение...</p></WikidotModal>}
                {error && (
                    <WikidotModal buttons={[{title: 'Закрыть', onClick: this.onCloseError}]} isError>
                        <p><strong>Ошибка:</strong> {error}</p>
                    </WikidotModal>
                )}
                {canEdit && <a href="#" onClick={this.onEdit} className="btn btn-default btn-small btn-sm">Редактировать название и описание</a>}
                {' '}
                {canPin && <a href="#" onClick={this.onPin} className="btn btn-default btn-small btn-sm">{isPinned ? 'Открепить' : 'Закрепить'}</a>}
                {' '}
                {canLock && <a href="#" onClick={this.onLock} className="btn btn-default btn-small btn-sm">{isLocked ? 'Разблокировать' : 'Заблокировать'}</a>}
                {' '}
                {canMove && <a href="#" onClick={this.onMove} className="btn btn-default btn-small btn-sm">Переместить</a>}
            </>
        )
    }
}


export default ForumThreadOptions