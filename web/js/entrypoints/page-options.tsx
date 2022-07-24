import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { Component } from 'react';
import ArticleEditor from "../articles/article-editor";
import ArticleHistory from "../articles/article-history";
import ArticleSource from "../articles/article-source";
import ArticleTags from "../articles/article-tags";
import ArticleRating from "../articles/article-rating";
import ArticleParent from "../articles/article-parent";
import ArticleRename from "../articles/article-rename";
import ArticleLock from "../articles/article-lock";
import ArticleFiles from "../articles/article-files";
import ArticleDelete from "../articles/article-delete";
import {RatingMode} from '../api/rate'
import {sprintf} from 'sprintf-js'


interface Props {
    pageId?: string
    optionsEnabled?: boolean
    editable?: boolean
    lockable?: boolean
    rating?: number
    ratingVotes?: number
    ratingMode?: RatingMode
    pathParams?: { [key: string]: string }
    canRate?: boolean
}


interface State {
    subView: 'edit' | 'rating' | 'tags' | 'history' | 'source' | 'parent' | 'lock' | 'rename' | 'files' | 'delete' | null
    extOptions: boolean
}


class PageOptions extends Component<Props, State> {
    state = {
        subView: null,
        extOptions: false
    };

    onEdit = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({ subView: 'edit' });
        setTimeout(() => {
            window.scrollTo(window.scrollX, document.body.scrollHeight);
        }, 1);
    };

    onRate = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({ subView: 'rating' });
        setTimeout(() => {
            window.scrollTo(window.scrollX, document.body.scrollHeight);
        }, 1);
    }

    onTags = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({ subView: 'tags' });
        setTimeout(() => {
            window.scrollTo(window.scrollX, document.body.scrollHeight);
        }, 1);
    };

    onCancelSubView = () => {
        this.setState({ subView: null });
    };

    onHistory = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({ subView: 'history' });
        setTimeout(() => {
            window.scrollTo(window.scrollX, document.body.scrollHeight);
        });
    };

    onFiles = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({ subView: 'files' });
        setTimeout(() => {
            window.scrollTo(window.scrollX, document.body.scrollHeight);
        });
    };

    onSource = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({ subView: 'source' });
        setTimeout(() => {
            window.scrollTo(window.scrollX, document.body.scrollHeight);
        });
    };

    onParent = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({ subView: 'parent' });
        setTimeout(() => {
            window.scrollTo(window.scrollX, document.body.scrollHeight);
        });
    };

    onLock = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({ subView: 'lock' });
        setTimeout(() => {
            window.scrollTo(window.scrollX, document.body.scrollHeight);
        });
    };

    onRename = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({ subView: 'rename' });
        setTimeout(() => {
            window.scrollTo(window.scrollX, document.body.scrollHeight);
        });
    };

    onDelete = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({ subView: 'delete' });
        setTimeout(() => {
            window.scrollTo(window.scrollX, document.body.scrollHeight);
        });
    };

    toggleExtOptions = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({ extOptions: !this.state.extOptions });
    };

    renderRating() {
        const { rating, ratingMode } = this.props;

        if (ratingMode === 'updown') {
            return sprintf("%+d", rating)
        } else if (ratingMode === 'stars') {
            return sprintf("%.1f", rating)
        } else {
            return 'n/a'
        }
    }

    render() {
        const { optionsEnabled, editable, lockable, rating, canRate } = this.props;
        const { extOptions } = this.state;

        if (!optionsEnabled) {
            return null
        }

        return (
            <>
                <div id="page-options-bottom" className="page-options-bottom">
                    { editable && <a id="edit-button" className="btn btn-default" href="#" onClick={this.onEdit}>Редактировать</a> }
                    <a id="pagerate-button" className="btn btn-default" href="#" onClick={this.onRate}>{canRate?'Оценить':'Оценки'} ({this.renderRating()})</a>
                    { editable && <a id="tags-button" className="btn btn-default" href="#" onClick={this.onTags}>Теги</a> }
                    <a id="history-button" className="btn btn-default" href="#" onClick={this.onHistory}>История</a>
                    <a id="files-button" className="btn btn-default" href="#" onClick={this.onFiles}>Файлы</a>
                    <a id="more-options-button" className="btn btn-default" href="#" onClick={this.toggleExtOptions}>{extOptions?'- Опции':'+ Опции'}</a>
                </div>
                { extOptions && <div id="page-options-bottom-2" className="page-options-bottom form-actions">
                    <a id="view-source-button" className="btn btn-default" href="#" onClick={this.onSource}>Исходник страницы</a>
                    { editable && <a id="parent-page-button" className="btn btn-default" href="#" onClick={this.onParent}>Родитель</a> }
                    { lockable && <a id="page-block-button" className="btn btn-default" href="#" onClick={this.onLock}>Заблокировать страницу</a> }
                    { editable && <a id="rename-move-button" className="btn btn-default" href="#" onClick={this.onRename}>Переименовать</a> }
                    { editable && <a id="delete-button" className="btn btn-default" href="#" onClick={this.onDelete}>Удалить</a> }
                </div> }
                { this.renderSubView() }
            </>
        )
    }

    renderSubView() {
        return ReactDOM.createPortal(this.pickSubView(), document.getElementById('action-area'));
    }

    pickSubView() {
        const { subView } = this.state;
        const { pageId, rating, pathParams, editable } = this.props;

        switch (subView) {
            case 'edit':
                return <ArticleEditor pageId={pageId} pathParams={pathParams} onClose={this.onCancelSubView} />;

            case 'rating':
                return <ArticleRating pageId={pageId} rating={rating} onClose={this.onCancelSubView} />;

            case 'tags':
                return <ArticleTags pageId={pageId} onClose={this.onCancelSubView} />;

            case 'history':
                return <ArticleHistory pageId={pageId} pathParams={pathParams} onClose={this.onCancelSubView} />;

            case 'source':
                return <ArticleSource pageId={pageId} onClose={this.onCancelSubView} />;

            case 'parent':
                return <ArticleParent pageId={pageId} onClose={this.onCancelSubView} />;

            case 'lock':
                return <ArticleLock pageId={pageId} onClose={this.onCancelSubView} />;

            case 'rename':
                return <ArticleRename pageId={pageId} onClose={this.onCancelSubView} />;

            case 'files':
                return <ArticleFiles pageId={pageId} onClose={this.onCancelSubView} editable={editable} />;

            case 'delete':
                return <ArticleDelete pageId={pageId} onClose={this.onCancelSubView} />;

            default:
                return null
        }
    }
}


export default PageOptions