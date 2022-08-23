import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { Component } from 'react';
import ArticleEditor from '../articles/article-editor';


interface Props {
    page_id?: string
}

interface State {
    isCreate: boolean
}


class Page404 extends Component<Props, State> {
    state = {
        isCreate: false
    };

    onCreate = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({isCreate: true});
        const { page_id } = this.props;
        ReactDOM.render(<ArticleEditor pageId={page_id} isNew onClose={this.onCancel} />, document.getElementById("action-area"))
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
