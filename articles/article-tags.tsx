import * as React from 'react';
import { Component } from 'react';
import styled from "styled-components";
import WikidotModal from "../util/wikidot-modal";
import sleep from "../util/async-sleep";
import {fetchArticle, updateArticle} from "../api/articles";
import {fetchAllTags, FetchAllTagsResponse} from '../api/tags'
import TagEditorComponent from '../components/tag-editor'
import Loader from '../util/loader'


interface Props {
    pageId: string
    isNew?: boolean
    onClose?: () => void
    canCreateTags?: boolean
}

interface State {
    tags: Array<string>
    allTags: FetchAllTagsResponse | null
    loading: boolean
    saving: boolean
    savingSuccess?: boolean
    error?: string
    fatalError?: boolean
}


const Styles = styled.div`
.text {  
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
  
.w-tag-editor-container {
  position: relative;
}
  
/* fixes BHL; without table this looks bad */
table.form {
  display: table !important;
}
  
.form tr {
  display: table-row !important;
}
  
.form td, th {
  display: table-cell !important;
}
`;


class ArticleTags extends Component<Props, State> {
    constructor(props) {
        super(props);
        this.state = {
            tags: [],
            allTags: null,
            loading: true,
            saving: false
        }
    }

    async componentDidMount() {
        const { pageId } = this.props;
        this.setState({ loading: true });
        try {
            const [data, allTags] = await Promise.all([fetchArticle(pageId), fetchAllTags()]);
            this.setState({ loading: false, tags: data.tags, allTags: allTags });
        } catch (e) {
            this.setState({loading: false, fatalError: true, error: e.error || 'Ошибка связи с сервером'});
        }
    }

    onSubmit = async (e) => {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }

        const { pageId } = this.props;
        this.setState({ saving: true, error: null, savingSuccess: false });
        const input = {
            pageId: this.props.pageId,
            tags: this.state.tags
        };
        try {
            await updateArticle(pageId, input);
            this.setState({ saving: false, savingSuccess: true });
            await sleep(1000);
            this.setState({ savingSuccess: false });
            window.scrollTo(window.scrollX, 0);
            window.location.reload();
        } catch (e) {
            this.setState({ saving: false, fatalError: false, error: e.error || 'Ошибка связи с сервером' });
        }
    };

    onClear = (e) => {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        this.setState({ tags: [] })
    }

    onCancel = (e) => {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        if (this.props.onClose)
            this.props.onClose()
    };

    onCloseError = () => {
        const { fatalError } = this.state;
        this.setState({error: null});
        if (fatalError) {
            this.onCancel(null);
        }
    };

    onChange = (tags: Array<string>) => {
        this.setState({ tags });
    };

    render() {
        const { canCreateTags } = this.props;
        const { tags, allTags, loading, saving, savingSuccess, error } = this.state;
        return (
            <Styles>
                { saving && <WikidotModal isLoading><p>Сохранение...</p></WikidotModal> }
                { savingSuccess && <WikidotModal><p>Успешно сохранено!</p></WikidotModal> }
                { error && (
                    <WikidotModal buttons={[{title: 'Закрыть', onClick: this.onCloseError}]} isError>
                        <p><strong>Ошибка:</strong> {error}</p>
                    </WikidotModal>
                ) }
                <a className="action-area-close btn btn-danger" href="#" onClick={this.onCancel}>Закрыть</a>
                <h1>Теги страницы</h1>
                <p>Теги (метки) это хороший способ для организации содержимого на сайте, для создания "горизонтальной навигации" между связанными по смыслу страницами. Вы можете добавить несколько тегов к каждой из ваших страниц. Читайте подробнее про <a href="http://ru.wikipedia.org/wiki/%D0%A2%D0%B5%D0%B3" target="_blank"> теги</a>, про <a href="http://ru.wikipedia.org/wiki/%D0%9E%D0%B1%D0%BB%D0%B0%D0%BA%D0%BE_%D1%82%D0%B5%D0%B3%D0%BE%D0%B2" target="_blank">облако тегов </a></p>

                <form method="POST" onSubmit={this.onSubmit}>
                    <table className="form">
                        <tbody>
                        <tr>
                            <td>
                                Теги:
                            </td>
                        </tr>
                        <tr>
                            <td className="w-tag-editor-container">
                                { loading && <Loader className="loader" /> }
                                <TagEditorComponent canCreateTags={canCreateTags} tags={tags} allTags={allTags || {categories: [], tags: []}} onChange={this.onChange} />
                            </td>
                        </tr>
                        </tbody>
                    </table>
                    <div className="buttons form-actions">
                        <input type="button" className="btn btn-danger" value="Закрыть" onClick={this.onCancel} />
                        <input type="button" className="btn btn-default" value="Очистить" onClick={this.onClear} />
                        <input type="button" className="btn btn-primary" value="Сохранить теги" onClick={this.onSubmit}/>
                    </div>
                </form>
            </Styles>
        )
    }
}


export default ArticleTags