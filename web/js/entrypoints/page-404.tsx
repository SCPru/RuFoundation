import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { Component } from 'react';
import ArticleEditor from '../articles/article-editor';
import styled from 'styled-components'


interface Props {
    page_id?: string
}

interface State {
    isCreate: boolean
}


class Page404 extends Component<Props, State> {
    state = {
        isCreate: false,
        bodyRef: null
    };

    onCreate = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({isCreate: true});
        setTimeout(() => window.scrollTo(0, document.body.scrollHeight), 0);
        (window as any)._openNewEditor(() => {
            this.setState({isCreate: false});
        });
    };

    onCancel = () => {
        this.setState({isCreate: false});
    };

    render() {
        const { isCreate } = this.state;
        const { page_id } = this.props;
        if (!isCreate) {
            return (
                <>
                    <p id="404-message">
                        Запрашиваемая вами страница <em>{page_id}</em> не существует.
                    </p>
                    <ul id="create-it-now-link">
                        <li>
                            <a href="#" onClick={this.onCreate}>Создать страницу</a>
                        </li>
                    </ul>
                </>
            )
        }
    }
}


export default Page404