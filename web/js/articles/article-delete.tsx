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
            if (!permanent) {
                const input = {
                    pageId: new_name,
                    tags: []
                };
                await updateArticle(pageId, input);
            } else {
                await deleteArticle(pageId)
            }
            this.setState({ saving: false, savingSuccess: true });
            await sleep(1000);
            this.setState({ savingSuccess: false });
            window.scrollTo(window.scrollX, 0);
            if (!permanent) {
                window.location.href = `/${new_name}`;
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
                <p>Вы можете удалить страницу, либо переместив её в категорию "deleted", либо удалить её навсегда (это безвозвратно, будьте осторожны).</p>


                <table className="form">
                    <tbody>
                    <tr>
                        <td>
                            Что делать?
                        </td>
                        <td>
                            <input type="checkbox" name="permanent" className={`text ${loading?'loading':''}`} onChange={this.onChange} id="page-rename-input" checked={!permanent||!canDelete} disabled={loading||saving||!canDelete}/>
                            <label htmlFor="page-rename-input">Переименовать</label>
                        </td>
                    </tr>
                    {canDelete&&<tr>
                        <td>
                        </td>
                        <td>
                            <input type="checkbox" name="permanent" className={`text ${loading?'loading':''}`} onChange={this.onChange} id="page-permanent-input" checked={permanent} disabled={loading||saving}/>
                            <label htmlFor="page-permanent-input">Удалить навсегда</label>
                        </td>
                    </tr>}
                    </tbody>
                </table>

                {!permanent ? (
                    <form method="POST" onSubmit={this.onSubmit}>
                        <p>Установив странице префикс "deleted:" вы переместите её в другую категорию(пространство имен). Это более-менее эквивалентно удалению, но информация не будет потеряна.</p>
                        <table className="form">
                            <tbody>
                            <tr>
                                <td>
                                    Название страницы:
                                </td>
                                <td>
                                    {pageId}
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    Новое название страницы:
                                </td>
                                <td>
                                    <input type="text" name="new_name" className={`text ${loading?'loading':''}`} onChange={this.onChange} id="page-rename-input" defaultValue={new_name} disabled={loading||saving}/>
                                </td>
                            </tr>
                            </tbody>
                        </table>
                        <div className="buttons form-actions">
                            <input type="button" className="btn btn-danger" value="Закрыть" onClick={this.onCancel} />
                            <input type="button" className="btn btn-primary" value="Переименовать/переместить" onClick={this.onSubmit}/>
                        </div>
                    </form>
                ) : (
                    <form method="POST" onSubmit={this.onSubmit}>
                        <p>Это приведет к полному удалению страницы и невозможности восстановления данных. Вы уверены, что хотите это сделать?</p>
                        <div className="buttons form-actions">
                            <input type="button" className="btn btn-danger" value="Закрыть" onClick={this.onCancel} />
                            <input type="button" className="btn btn-primary" value="Удалить" onClick={this.onSubmit}/>
                        </div>
                    </form>
                )}
            </Styles>
        )
    }
}


export default ArticleDelete