import * as React from 'react';
import { Component } from 'react';
import {fetchArticle} from "../api/articles";
import WikidotModal from "../util/wikidot-modal";
import styled from "styled-components";
import Loader from "../util/loader";


interface Props {
    pageId: string
    onClose: () => void
    source?: string
}


interface State {
    loading: boolean
    source?: string
    error?: string
}


const Styles = styled.div<{loading?: boolean}>`
#source-code.loading {
  position: relative;
  min-height: calc(32px + 16px + 16px);
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

textarea {
  width: 100%;
  min-height: 600px;
}
`;


class ArticleSource extends Component<Props, State> {

    constructor(props) {
        super(props);
        this.state = {
            loading: false,
            source: this.props.source
        };
    }

    componentDidMount() {
        this.loadSource();
    }

    async loadSource() {
        const { pageId, source } = this.props;
        if (!source) {
            this.setState({ loading: true, error: null });
            try {
                const article = await fetchArticle(pageId);
                this.setState({ loading: false, error: null, source: article.source });
            } catch (e) {
                this.setState({ loading: false, error: e.error || 'Ошибка связи с сервером' });
            }
        }
    }

    onClose = (e) => {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        if (this.props.onClose)
            this.props.onClose();
    };

    onCloseError = () => {
        this.setState({error: null});
        this.onClose(null);
    };

    render() {
        const { error, loading, source } = this.state;
        return (
            <Styles>
                { error && (
                    <WikidotModal buttons={[{title: 'Закрыть', onClick: this.onCloseError}]} isError>
                        <p><strong>Ошибка:</strong> {error}</p>
                    </WikidotModal>
                ) }
                <a className="action-area-close btn btn-danger" href="#" onClick={this.onClose}>Закрыть</a>
                <h1>Исходник страницы</h1>
                <div id="source-code" className={`${loading?'loading':''}`}>
                    { loading && <Loader className="loader" /> }
                    <textarea value={source||''} readOnly />
                </div>
            </Styles>
        )
    }
}


export default ArticleSource