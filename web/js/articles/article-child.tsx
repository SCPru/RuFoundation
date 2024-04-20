import * as React from 'react';
import { Component } from 'react';
import styled from "styled-components";
import WikidotModal from "../util/wikidot-modal";
import { isFullNameAllowed } from '../util/validate-article-name';


interface Props {
    pageId: string
    isNew?: boolean
    onClose?: () => void
}

interface State {
    child: string
    error?: string
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


class ArticleChild extends Component<Props, State> {
    constructor(props) {
        super(props);
        this.state = {
            child: ''
        }
    }

    onSubmit = async (e) => {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }

        const { pageId } = this.props;
        let { child } = this.state;

        if (isFullNameAllowed(child)) {
            window.location.href = `/${child}/edit/true/parent/${pageId}`;
        } else {
            this.setState({ error: 'Некорректный ID дочерней страницы!' });
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
        // @ts-ignore
        this.setState({[e.target.name]: e.target.value})
    };

    onCloseError = () => {
        this.setState({error: undefined});
    };

    render() {
        const { pageId } = this.props;
        const { child, error } = this.state;
        return (
            <Styles>
                { error && (
                    <WikidotModal buttons={[{title: 'Закрыть', onClick: this.onCloseError}]} isError>
                        <p><strong>Ошибка:</strong> {error}</p>
                    </WikidotModal>
                ) }
                <a className="action-area-close btn btn-danger" href="#" onClick={this.onCancel}>Закрыть</a>
                <h1>Создать дочернюю страницу</h1>
                <p>Это действие создаст страницу, в качестве родителя которой будет установлена данная страница.</p>
                <p>Это полезно например при создании оффсетов.</p>

                <form method="POST" onSubmit={this.onSubmit}>
                    <table className="form">
                        <tbody>
                        <tr>
                            <td>
                                Название этой страницы:
                            </td>
                            <td>
                                {pageId}
                            </td>
                        </tr>
                        <tr>
                            <td>
                                Название дочерней страницы:
                            </td>
                            <td>
                                <input type="text" name="child" className="text" onChange={this.onChange} id="page-child-input" defaultValue={child}/>
                            </td>
                        </tr>
                        </tbody>
                    </table>
                    <div className="buttons form-actions">
                        <input type="button" className="btn btn-danger" value="Закрыть" onClick={this.onCancel} />
                        <input type="button" className="btn btn-primary" value="Создать" onClick={this.onSubmit}/>
                    </div>
                </form>
            </Styles>
        )
    }
}


export default ArticleChild