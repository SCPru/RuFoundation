import * as React from 'react';
import { Component } from 'react';
import ArticleEditor from "../articles/article-editor";


interface Props {
    pageId?: string
    optionsEnabled?: boolean
    editable?: boolean
}


interface State {
    subView: 'edit' | null
}


class PageOptions extends Component<Props, State> {
    state = {
        subView: null
    };

    onEdit = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({ subView: 'edit' });
        setTimeout(() => {
            window.scrollTo(window.scrollX, document.body.scrollHeight);
        }, 1);
    };

    onCancelEdit = () => {
        this.setState({ subView: null });
    };

    render() {
        const { optionsEnabled, editable } = this.props;
        const { subView } = this.state;

        if (!optionsEnabled) {
            return null
        }

        return (
            <>
                <div id="page-options-bottom" className="page-options-bottom">
                    { editable && <a id="edit-button" className="btn btn-default" href="#" onClick={this.onEdit}>Редактировать</a> }
                </div>
                { subView && (
                    <div id="action-area">
                        { this.renderSubView() }
                    </div>
                ) }
            </>
        )
    }

    renderSubView() {
        const { subView } = this.state;
        const { pageId } = this.props;

        switch (subView) {
            case 'edit':
                return <ArticleEditor pageId={pageId} onCancel={this.onCancelEdit} />;

            default:
                return null
        }
    }
}


export default PageOptions