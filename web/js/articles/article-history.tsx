import * as React from 'react';
import { Component } from 'react';


interface Props {
    pageId: string
    onClose: () => void
}


interface State {

}


class ArticleHistory extends Component<Props, State> {

    onClose = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (this.props.onClose)
            this.props.onClose();
    };

    render() {
        return (
            <>
                <a className="action-area-close btn btn-danger" href="#" onClick={this.onClose}>Закрыть</a>
                <h1>История изменений</h1>
            </>
        )
    }

}


export default ArticleHistory