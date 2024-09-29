import * as React from 'react';
import { Component } from 'react';
import styled from "styled-components";
import WikidotModal from "../util/wikidot-modal";
import sleep from "../util/async-sleep";
import {deleteArticle, fetchArticle, updateArticle} from "../api/articles";


interface Props {
    pageId: string
    isNew?: boolean
    onClose?: () => void
    canDelete?: boolean
}

interface State {
    permanent: boolean
    new_name: string
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
`;


class ArticleDelete extends Component<Props, State> {
    constructor(props) {
        super(props);
        this.state = {
            permanent: false,
            new_name: "deleted:" + this.props.pageId,
            loading: true,
            saving: false
        }
    }

    async componentDidMount() {
        const { pageId } = this.props;
        this.setState({ loading: true });
        try {
            const data = await fetchArticle(pageId);
            this.setState({ loading: false, new_name: "deleted:" + data.pageId});
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
        const { permanent, new_name } = this.state;
        this.setState({ saving: true, error: null, savingSuccess: false });
        try {
            let actualNewName = new_name
            if (!permanent) {
                const input = {
                    pageId: new_name,
                    tags: [],
                    forcePageId: true
                };
                const result = await updateArticle(pageId, input);
                actualNewName = result.pageId
            } else {
                await deleteArticle(pageId)
            }
            this.setState({ saving: false, savingSuccess: true });
            await sleep(1000);
            this.setState({ savingSuccess: false });
            window.scrollTo(window.scrollX, 0);
            if (!permanent) {
                window.location.href = `/${actualNewName}`;
            } else {
                window.location.reload();
            }
        } catch (e) {
            this.setState({ saving: false, fatalError: false, error: e.error || 'Ошибка связи с сервером' });
        }
    };

    onCancel = (e) => {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        if (this.props.onClose)
            this.props.onClose()
    };

    onChange = (e) => {
        if(e.target.type === 'checkbox'){
            // @ts-ignore
            this.setState({ ["permanent"]: !this.state.permanent});
        }
        else {
            // @ts-ignore
            this.setState({ [e.target.name]: e.target.value});
        }
    };

    onCloseError = () => {
        const { fatalError } = this.state;
        this.setState({error: null});
        if (fatalError) {
            this.onCancel(null);
        }
    };

    render() {
        const { pageId, canDelete } = this.props;
        const { permanent, new_name, loading, saving, savingSuccess, error } = this.state;

        const isAlreadyDeleted = pageId.toLowerCase().startsWith('deleted:')

        if (isAlreadyDeleted && !canDelete) {
            return (
                <Styles>
                    <a className="action-area-close btn btn-danger" href="#" onClick={this.onCancel}>Закрыть</a>
                    <h1>Удалить страницу</h1>
                    <p>
                        Эта страница уже считается удалённой, поскольку находится в категории "deleted". Вы не можете удалить её ещё сильнее.
                    </p>
                </Styles>
            )
        }

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
                <h1>Удалить страницу</h1>
                {canDelete ? (
                    <p>Вы можете удалить страницу, либо переместив её в категорию "deleted", либо удалить её навсегда (это безвозвратно, будьте осторожны).</p>
                ) : (
                    <p>Вы можете удалить страницу, переместив её в категорию "deleted". Полное удаление недоступно.</p>
                )}

                {canDelete&&<table className="form">
                    <tbody>
                    <tr>
                        <td>
                            Что делать?
                        </td>
                        <td>
                            <input type="checkbox" name="permanent" className={`text ${loading?'loading':''}`} onChange={this.onChange} id="page-rename-input" checked={!permanent} disabled={loading||saving||!canDelete}/>
                            <label htmlFor="page-rename-input">Переименовать</label>
                        </td>
                    </tr>
                    <tr>
                        <td>
                        </td>
                        <td>
                            <input type="checkbox" name="permanent" className={`text ${loading?'loading':''}`} onChange={this.onChange} id="page-permanent-input" checked={permanent} disabled={loading||saving}/>
                            <label htmlFor="page-permanent-input">Удалить навсегда</label>
                        </td>
                    </tr>
                    </tbody>
                </table>}

                {!permanent ? (
                    <form method="POST" onSubmit={this.onSubmit}>
                        <p>Установив странице префикс "deleted:" вы переместите её в другую категорию (пространство имён). Это более-менее эквивалентно удалению, но информация не будет потеряна.</p>
                        {isAlreadyDeleted && <p><strong>Внимание:</strong> Статья уже находится в категории "deleted". Если вы хотите удалить её ещё сильнее, воспользуйтесь опцией "Удалить навсегда".</p>}
                        <div className="buttons form-actions">
                            <input type="button" className="btn btn-danger" value="Отмена" onClick={this.onCancel} />
                            {!isAlreadyDeleted && <input type="button" className="btn btn-primary" value={'Переместить в категорию "deleted"'} onClick={this.onSubmit}/>}
                        </div>
                    </form>
                ) : (
                    <form method="POST" onSubmit={this.onSubmit}>
                        <p>Это приведет к полному удалению страницы и невозможности восстановления данных. Вы уверены, что хотите это сделать?</p>
                        <div className="buttons form-actions">
                            <input type="button" className="btn btn-danger" value="Отмена" onClick={this.onCancel} />
                            <input type="button" className="btn btn-primary" value="Удалить" onClick={this.onSubmit}/>
                        </div>
                    </form>
                )}
            </Styles>
        )
    }
}


export default ArticleDelete