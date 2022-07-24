import * as React from 'react';
import { Component } from 'react';
import {ArticleLogEntry, fetchArticleLog, fetchArticleVersion} from "../api/articles";
import WikidotModal, {showRevertModal} from "../util/wikidot-modal";
import sleep from "../util/async-sleep";
import styled from "styled-components";
import Loader from "../util/loader";
import formatDate from "../util/date-format";
import UserView from "../util/user-view";
import {showVersionMessage} from "../util/wikidot-message";
import ArticleSource from "./article-source";
import Pagination from '../util/pagination'


interface Props {
    pageId: string
    pathParams?: { [key: string]: string }
    onClose: () => void
}


interface State {
    loading: boolean
    entries?: Array<ArticleLogEntry>
    subarea?: JSX.Element
    entryCount: number
    page: number
    perPage: number
    error?: string
    fatalError?: boolean
}


const Styles = styled.div<{loading?: boolean}>`
#revision-list.loading {
  position: relative;
  min-height: calc(32px + 16px + 16px);
  &::after {
    content: ' ';
    position: absolute;
    background: #0000003f;
    z-index: 0;
    left: 0;
    right: 0;
    top: 0;
    bottom: 0;
  }
  .loader {
    position: absolute;
    left: 16px;
    top: 16px;
    z-index: 1;
  }
}
.page-history {
  tr td {
    &:nth-child(2) {
      width: 5em;
    }
    &:nth-child(4) {
      width: 5em;
    }
    &:nth-child(5) {
      width: 15em;
    }
    &:nth-child(6) {
      padding: 0 0.5em;
      width: 12em;
    }
    &:nth-child(7) {
      font-size: 90%;
    }
    .action {
      border: 1px solid #BBB;
      padding: 0 3px;
      text-decoration: none;
      color: #824;
      background: transparent;
      cursor: pointer;
    }
  }
}
`;


class ArticleHistory extends Component<Props, State> {

    constructor(props) {
        super(props);
        this.state = {
            loading: false,
            entries: null,
            subarea: null,
            entryCount: 0,
            page: 1,
            perPage: 25
        };
    }

    componentDidMount() {
        this.loadHistory();
    }

    async loadHistory(nextPage?: number) {
        const { pageId } = this.props;
        const { page, perPage, entries } = this.state;
        this.setState({ loading: true, error: null });
        try {
            const realPage = nextPage || page;
            const from = (realPage-1) * perPage;
            const to = (realPage) * perPage;
            const history = await fetchArticleLog(pageId, from, to);
            this.setState({ loading: false, error: null, entries: history.entries, entryCount: history.count, page: realPage });
        } catch (e) {
            this.setState({ loading: false, fatalError: entries === null, error: e.error || 'Ошибка связи с сервером' });
        }
    }

    onClose = (e) => {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        if (this.props.onClose)
            this.props.onClose();
    };

    onCloseError = () => {
        const { fatalError } = this.state;
        this.setState({error: null});
        if (fatalError) {
            this.onClose(null);
        }
    };

    onChangePage = (nextPage) => {
        this.loadHistory(nextPage);
    }

    render() {
        const { error, entries, entryCount, page, perPage, subarea, loading } = this.state;

        const totalPages = Math.ceil(entryCount / perPage);

        return (
            <Styles>
                { error && (
                    <WikidotModal buttons={[{title: 'Закрыть', onClick: this.onCloseError}]}>
                        <strong>Ошибка:</strong> {error}
                    </WikidotModal>
                ) }
                <a className="action-area-close btn btn-danger" href="#" onClick={this.onClose}>Закрыть</a>
                <h1>История изменений</h1>
                <div id="revision-list" className={`${loading?'loading':''}`}>
                    { loading && <Loader className="loader" /> }
                    { entries && (totalPages>1) && (
                        <Pagination page={page} maxPages={totalPages} onChange={this.onChangePage} />
                    ) }
                    { entries && (
                        <table className="page-history">
                            <tbody>
                            <tr>
                                <td>рев.</td>
                                <td>&nbsp;</td>
                                <td>флаги</td>
                                <td>действия</td>
                                <td>от</td>
                                <td>дата</td>
                                <td>комментарии</td>
                            </tr>
                            { entries.map(entry => {
                                return (
                                    <tr key={entry.revNumber}>
                                        <td>
                                            {entry.revNumber}.
                                        </td>
                                        <td>&nbsp;</td>
                                        <td>
                                            {this.renderFlags(entry)}
                                        </td>
                                        <td>
                                            {this.renderActions(entry)}
                                        </td>
                                        <td>
                                            {this.renderUser(entry)}
                                        </td>
                                        <td>
                                            {this.renderDate(entry)}
                                        </td>
                                        <td>
                                            {this.renderComment(entry)}
                                        </td>
                                    </tr>
                                )
                            }) }
                            </tbody>
                        </table>
                    ) }
                </div>
                <div id="history-subarea">
                    {subarea}
                </div>
            </Styles>
        )
    }

    renderFlags(entry: ArticleLogEntry) {
        switch (entry.type) {
            case 'new':
                return <span className="spantip" title="создана новая страница">N</span>;

            case 'title':
                return <span className="spantip" title="изменился заголовок">T</span>;

            case 'source':
                return <span className="spantip" title="изменился текст статьи">S</span>;

            case 'tags':
                return <span className="spantip" title="метки изменились">A</span>;

            case 'name':
                return <span className="spantip" title="страница переименована/удалена">R</span>;

            case 'parent':
                return <span className="spantip" title="изменилась родительская страница">M</span>;

            case 'file_added':
            case 'file_deleted':
            case 'file_renamed':
                return <span className="spantip" title="действия с файлом/вложением">F</span>

            case 'wikidot':
                return <span className="spantip" title="правка, портированная с Wikidot">W</span>
        }
    }

    renderActions (entry: ArticleLogEntry) {
        if (entry.type === 'wikidot') {
            return null;
        }
        return <>
            <button className={"action"} onClick={() => this.displayArticleVersion(entry)} title="Просмотр изменений страницы">V</button>
            <button className={"action"} onClick={() => this.displayVersionSource(entry)} title="Просмотр источника изменений">S</button>
            {this.state.entryCount !== (entry.revNumber+1) && <button className={"action"} onClick={() => this.revertArticleVersion(entry)} title="Вернуться к правке">R</button>}
        </>;
    }

    renderUser (entry: ArticleLogEntry) {
        return <UserView data={entry.user} />;
    }

    renderDate(entry: ArticleLogEntry) {
        return formatDate(new Date(entry.createdAt));
    }

    renderComment(entry: ArticleLogEntry) {
        if (entry.comment.trim()) {
            return entry.comment;
        }
        switch (entry.type) {
            case 'new':
                return 'Создание новой страницы';

            case 'title':
                return <>Заголовок изменён с "<em>{entry.meta.prev_title}</em>" на "<em>{entry.meta.title}</em>"</>;

            case 'name':
                return <>Страница переименована из "<em>{entry.meta.prev_name}</em>" в "<em>{entry.meta.name}</em>"</>;

            case 'tags':
                if (Array.isArray(entry.meta.added_tags) && entry.meta.added_tags.length && Array.isArray(entry.meta.removed_tags) && entry.meta.removed_tags.length) {
                    return <>Добавлены теги: {entry.meta.added_tags.join(', ')}. Удалены теги: {entry.meta.removed_tags.join(', ')}.</>;
                } else if (Array.isArray(entry.meta.added_tags) && entry.meta.added_tags.length) {
                    return <>Добавлены теги: {entry.meta.added_tags.join(', ')}.</>;
                } else if (Array.isArray(entry.meta.removed_tags) && entry.meta.removed_tags.length) {
                    return <>Удалены теги: {entry.meta.removed_tags.join(', ')}.</>;
                }
                break;

            case 'parent':
                if (entry.meta.prev_parent && entry.meta.parent) {
                    return <>Родительская страница изменена с "<em>{entry.meta.prev_parent}</em>" на
                        "<em>{entry.meta.parent}</em>"</>;
                } else if (entry.meta.prev_parent) {
                    return <>Убрана родительская страница "<em>{entry.meta.prev_parent}</em>"</>;
                } else if (entry.meta.parent) {
                    return <>Установлена родительская страница "<em>{entry.meta.parent}</em>"</>;
                }
                break;

            case 'file_added':
                return <>Загружен файл: "<em>{entry.meta.name}</em>"</>;

            case 'file_deleted':
                return <>Удалён файл: "<em>{entry.meta.name}</em>"</>;

            case 'file_renamed':
                return <>Переименован файл: "<em>{entry.meta.prev_name}</em>" в "<em>{entry.meta.name}</em>"</>;
        }
    }

    displayArticleVersion (entry: ArticleLogEntry) {
        const { pageId, pathParams } = this.props;
        fetchArticleVersion(pageId, entry.revNumber, pathParams).then(function (resp) {
            showVersionMessage(entry.revNumber, new Date(entry.createdAt), entry.user, pageId);
            document.getElementById("page-content").innerHTML = resp.rendered;
        })
    }

    displayVersionSource (entry: ArticleLogEntry) {
        const { pageId, pathParams } = this.props;
        let onClose = this.hideSubArea;
        let show = this.showSubArea;
        fetchArticleVersion(pageId, entry.revNumber, pathParams).then(function (resp) {
            onClose();
            show(<ArticleSource pageId={pageId} onClose={onClose} source={resp.source} />);
        })
    }

    showSubArea = (component: JSX.Element) => {
        this.setState({subarea: component})
    }

    hideSubArea =  () => {
        this.setState({subarea: null})
    }

    revertArticleVersion (entry: ArticleLogEntry) {
        const {pageId} = this.props;
        showRevertModal(pageId, entry);
    }

}


export default ArticleHistory