import * as React from 'react';
import { Component } from 'react';
import styled from "styled-components";
import WikidotModal from "../util/wikidot-modal";
import sleep from "../util/async-sleep";
import {fetchArticle, updateArticle} from "../api/articles";


interface Props {
    pageId: string
    isNew?: boolean
    onClose?: () => void
}

interface State {
    locked: boolean
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


class ArticleLock extends Component<Props, State> {
    constructor(props) {
        super(props);
        this.state = {
            locked: false,
            loading: true,
            saving: false
        }
    }

    async componentDidMount() {
        const { pageId } = this.props;
        this.setState({ loading: true });
        try {
            const data = await fetchArticle(pageId);
            this.setState({ loading: false, locked: data.locked});
            console.log(this.state)
        } catch (e) {
            this.setState({loading: false, fatalError: true, error: e.error || 'Ошибка связи с сервером'});
        }
    }

    onSubmit = async () => {
        const { pageId } = this.props;
        this.setState({ saving: true, error: null, savingSuccess: false });
        const input = {
            pageId: pageId,
            locked: this.state.locked
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

    onCancel = () => {
        if (this.props.onClose)
            this.props.onClose()
    };

    onChange = (e) => {
        if(e.target.type === 'checkbox'){
            // @ts-ignore
            this.setState({ [e.target.name]: e.target.checked});
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
            this.onCancel();
        }
    };

    render() {
        const { locked, loading, saving, savingSuccess, error } = this.state;
        return (
            <Styles>
                { saving && <WikidotModal isLoading>Сохранение...</WikidotModal> }
                { savingSuccess && <WikidotModal>Успешно сохранено!</WikidotModal> }
                { error && (
                    <WikidotModal buttons={[{title: 'Закрыть', onClick: this.onCloseError}]}>
                        <strong>Ошибка:</strong> {error}
                    </WikidotModal>
                ) }
                <a className="action-area-close btn btn-danger" href="#" onClick={this.onCancel}>Закрыть</a>
                <h1>Заблокировать эту страницу</h1>
                <p>Когда страница заблокирована (защищена) только модераторы и администраторы сайта могут её редактировать. Это иногда полезно, например, для стартовой страницы.</p>

                <form method="POST" onSubmit={this.onSubmit}>
                    <table className="form">
                        <tbody>
                        <tr>
                            <td>
                                Страница защищена:
                            </td>
                            <td>
                                <input type="checkbox" name="locked" className={`text ${loading?'loading':''}`} onChange={this.onChange} id="page-locked-input" checked={locked} disabled={loading||saving}/>
                            </td>
                        </tr>
                        </tbody>
                    </table>
                    <div className="buttons form-actions">
                        <input type="button" className="btn btn-danger" value="Закрыть" onClick={this.onCancel} />
                        <input type="button" className="btn btn-primary" value="Сохранить" onClick={this.onSubmit}/>
                    </div>
                </form>
            </Styles>
        )
    }
}


export default ArticleLock