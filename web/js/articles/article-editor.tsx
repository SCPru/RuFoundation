import * as React from 'react';
import { Component } from 'react';
import Loader from "../util/loader";
import styled from "styled-components";
import WikidotModal from "../util/wikidot-modal";
import sleep from "../util/async-sleep";
import {makePreview} from "../api/preview";
import {removeMessage, showPreviewMessage} from "../util/wikidot-message"
import {createArticle, fetchArticle, updateArticle} from "../api/articles";


interface Props {
    pageId: string
    pathParams?: { [key: string]: string }
    isNew?: boolean
    onClose?: () => void
    previewTitleElement?: HTMLElement | (() => HTMLElement)
    previewBodyElement?: HTMLElement | (() => HTMLElement)
}

interface State {
    title: string
    source: string
    comment: string
    loading: boolean
    saving: boolean
    savingSuccess?: boolean
    error?: string
    fatalError?: boolean
    previewOriginalTitle?: string
    previewOriginalTitleDisplay?: string
    previewOriginalBody?: string
}


function guessTitle(pageId) {
    const pageIdSplit = pageId.split(':', 2);
    if (pageIdSplit.length === 2)
        pageId = pageIdSplit[1];
    else pageId = pageIdSplit[0];

    let result = '';
    let brk = true;
    for (let i = 0; i < pageId.length; i++) {
        let char = pageId[i];
        if (char === '-') {
            if (!brk) {
                result += ' ';
            }
            brk = true;
            continue;
        }
        if (brk) {
            char = char.toUpperCase();
            brk = false;
        } else {
            char = char.toLowerCase();
        }
        result += char;
    }
    return result;
}


function getElement(e: HTMLElement | (() => HTMLElement)) {
    if (typeof(e) === 'function') {
        return e();
    }
    return e;
}


const Styles = styled.div`
.editor-area {
  position: relative;
  
  &.loading {
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
}
`;


class ArticleEditor extends Component<Props, State> {
    constructor(props) {
        super(props);
        this.state = {
            title: props.isNew ? guessTitle(props.pageId) : '',
            source: '',
            comment: '',
            loading: true,
            saving: false,
            previewOriginalTitle: getElement(props.previewTitleElement)?.innerText,
            previewOriginalTitleDisplay: getElement(props.previewTitleElement)?.style?.display,
            previewOriginalBody: getElement(props.previewBodyElement)?.innerHTML
        }
    }

    async componentDidMount() {
        const { isNew, pageId } = this.props;
        if (!isNew) {
            this.setState({ loading: true });
            try {
                const data = await fetchArticle(pageId);
                this.setState({ loading: false, source: data.source, title: data.title });
            } catch (e) {
                this.setState({ loading: false, fatalError: true, error: e.error || 'Ошибка связи с сервером' });
            }
        } else {
            this.setState({ loading: false })
        }
    }

    onSubmit = async () => {
        const { isNew, pageId } = this.props;
        this.setState({ saving: true, error: null, savingSuccess: false });
        const input = {
            pageId: this.props.pageId,
            title: this.state.title,
            source: this.state.source,
            comment: this.state.comment
        };
        if (isNew) {
            try {
                await createArticle(input);
                this.setState({ saving: false, savingSuccess: true });
                await sleep(1000);
                this.setState({ savingSuccess: false });
                window.location.href = `/${pageId}`;
            } catch (e) {
                this.setState({ saving: false, fatalError: false, error: e.error || 'Ошибка связи с сервером' });
            }
        } else {
            try {
                await updateArticle(pageId, input);
                this.setState({ saving: false, savingSuccess: true });
                await sleep(1000);
                this.setState({ savingSuccess: false });
                window.scrollTo(window.scrollX, 0);
                window.location.href = `/${pageId}`;
            } catch (e) {
                this.setState({ saving: false, fatalError: false, error: e.error || 'Ошибка связи с сервером' });
            }
        }
    };

    onPreview = () => {
        const { previewTitleElement, previewBodyElement } = this.props;
        const data = {
            pageId: this.props.pageId,
            title: this.state.title,
            source: this.state.source,
            pathParams: this.props.pathParams,
        };
        makePreview(data).then(function (resp) {
            showPreviewMessage();
            getElement(previewTitleElement).innerText = resp.title;
            getElement(previewTitleElement).style.display = '';
            getElement(previewBodyElement).innerHTML = resp.content;
        });
    };

    onCancel = (e) => {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        removeMessage();
        const { previewTitleElement, previewBodyElement } = this.props;
        const { previewOriginalTitle, previewOriginalTitleDisplay, previewOriginalBody } = this.state;
        if (typeof(previewOriginalTitle) === 'string') {
            getElement(previewTitleElement).innerText = previewOriginalTitle;
            getElement(previewTitleElement).style.display = previewOriginalTitleDisplay;
        }
        if (typeof(previewOriginalBody) === 'string') {
            getElement(previewBodyElement).innerHTML = previewOriginalBody;
        }
        if (this.props.onClose)
            this.props.onClose()
    };

    onChange = (e) => {
        // @ts-ignore
        this.setState({[e.target.name]: e.target.value})
    };

    onCloseError = () => {
        const { fatalError } = this.state;
        this.setState({error: null});
        if (fatalError) {
            this.onCancel(null);
        }
    };

    render() {
        const { isNew } = this.props;
        const { title, source, comment, loading, saving, savingSuccess, error } = this.state;
        return (
            <Styles>
                { saving && <WikidotModal isLoading>Сохранение...</WikidotModal> }
                { savingSuccess && <WikidotModal>Успешно сохранено!</WikidotModal> }
                { error && (
                    <WikidotModal buttons={[{title: 'Закрыть', onClick: this.onCloseError}]}>
                        <strong>Ошибка:</strong> {error}
                    </WikidotModal>
                ) }
                { isNew ? <h1>Создать страницу</h1> : <h1>Редактировать страницу</h1> }
                <form id="edit-page-form" onSubmit={this.onSubmit}>
                    <table className="form" style={{ margin: '0.5em auto 1em 0' }}>
                        <tbody>
                        <tr>
                            <td>Заголовок страницы:</td>
                            <td>
                                <input id="edit-page-title" value={title} onChange={this.onChange} name="title" type="text" size={35} maxLength={128} style={{ fontWeight: 'bold', fontSize: '130%' }} disabled={loading||saving} />
                            </td>
                        </tr>
                        </tbody>
                    </table>
                    {/* This is not supported right now but we have to add empty div for BHL */}
                    <div id="wd-editor-toolbar-panel" className="wd-editor-toolbar-panel" />
                    <div className={`editor-area ${loading?'loading':''}`}>
                        <textarea id="edit-page-textarea" value={source} onChange={this.onChange} name="source" rows={20} cols={60} style={{ width: '95%' }} disabled={loading||saving} />
                        <p>Краткое описание изменений:</p>
                        <textarea id="edit-page-comments" value={comment} onChange={this.onChange} name="comment" rows={3} cols={20} style={{ width: '35%' }} disabled={loading||saving} />
                        { loading && <Loader className="loader" /> }
                    </div>
                    <div className="buttons alignleft">
                        <input id="edit-cancel-button" className="btn btn-danger" type="button" name="cancel" value="Отмена" onClick={this.onCancel} disabled={loading||saving} />
                        <input id="edit-preview-button" className="btn btn-primary" type="button" name="preview" value="Предпросмотр" onClick={this.onPreview} disabled={loading||saving} />
                        <input id="edit-save-button" className="btn btn-primary" type="button" name="save" value="Сохранить" onClick={this.onSubmit} disabled={loading||saving} />
                    </div>
                </form>
            </Styles>
        )
    }
}


export default ArticleEditor