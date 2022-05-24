import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { Component, ReactNode } from 'react';
import ArticleEditor from "../articles/article-editor";
import ArticleHistory from "../articles/article-history";
import ArticleSource from "../articles/article-source";


interface Props {
    pageId?: string
    optionsEnabled?: boolean
    editable?: boolean
}


interface State {
    subView: 'edit' | 'history' | 'source' | null
    extOptions: boolean
}


class PageOptions extends Component<Props, State> {
    state = {
        subView: null,
        extOptions: false
    };

    onEdit = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({ subView: 'edit' });
        setTimeout(() => {
            window.scrollTo(window.scrollX, document.body.scrollHeight);
        }, 1);
    };

    onCancelSubView = () => {
        this.setState({ subView: null });
    };

    onHistory = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({ subView: 'history' });
        setTimeout(() => {
            window.scrollTo(window.scrollX, document.body.scrollHeight);
        });
    };

    onSource = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({ subView: 'source' });
        setTimeout(() => {
            window.scrollTo(window.scrollX, document.body.scrollHeight);
        });
    };

    toggleExtOptions = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({ extOptions: !this.state.extOptions });
    };

    render() {
        const { optionsEnabled, editable } = this.props;
        const { extOptions } = this.state;

        if (!optionsEnabled) {
            return null
        }

        return (
            <>
                <div id="page-options-bottom" className="page-options-bottom">
                    { editable && <a id="edit-button" className="btn btn-default" href="#" onClick={this.onEdit}>Редактировать</a> }
                    <a id="history-button" className="btn btn-default" href="#" onClick={this.onHistory}>История</a>
                    <a id="more-options-button" className="btn btn-default" href="#" onClick={this.toggleExtOptions}>{extOptions?'- Опции':'+ Опции'}</a>
                </div>
                { extOptions && <div id="page-options-bottom-2" className="page-options-bottom form-actions">
                    <a id="view-source-button" className="btn btn-default" href="#" onClick={this.onSource}>Исходник страницы</a>
                </div> }
                { this.renderSubView() }
            </>
        )
    }

    renderSubView() {
        return ReactDOM.createPortal(this.pickSubView(), document.getElementById('action-area'));
    }

    pickSubView() {
        const { subView } = this.state;
        const { pageId } = this.props;

        switch (subView) {
            case 'edit':
                return <ArticleEditor pageId={pageId} onCancel={this.onCancelSubView} />;

            case 'history':
                return <ArticleHistory pageId={pageId} onClose={this.onCancelSubView} />;

            case 'source':
                return <ArticleSource pageId={pageId} onClose={this.onCancelSubView} />;

            default:
                return null
        }
    }
}


export default PageOptions