import * as React from 'react';
import { Component } from 'react';
import styled from "styled-components";
import WikidotModal from "../util/wikidot-modal";
import { ArticleBacklinks, fetchArticleBacklinks } from "../api/articles"


interface Props {
    pageId: string
    onClose?: () => void
}

interface State {
    loading: boolean
    data: ArticleBacklinks
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

class ArticleBacklinksView extends Component<Props, State> {
    constructor(props) {
        super(props);
        this.state = {
            loading: true,
            data: {
                children: [],
                links: [],
                includes: []
            }
        }
    }

    async componentDidMount() {
        const { pageId } = this.props;
        this.setState({ loading: true });
        try {
            const data = await fetchArticleBacklinks(pageId);
            this.setState({ loading: false, data });
        } catch (e) {
            this.setState({ loading: false, fatalError: true, error: e.error || 'Ошибка связи с сервером' });
        }
    }

    onCancel = (e) => {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        if (this.props.onClose)
            this.props.onClose()
    };

    onCloseError = () => {
        const { fatalError } = this.state;
        this.setState({error: null});
        if (fatalError) {
            this.onCancel(null);
        }
    };

    render() {
        const { loading, data, error } = this.state;
        return (
            <Styles>
                { error && (
                    <WikidotModal buttons={[{title: 'Закрыть', onClick: this.onCloseError}]}>
                        <strong>Ошибка:</strong> {error}
                    </WikidotModal>
                ) }
                <a className="action-area-close btn btn-danger" href="#" onClick={this.onCancel}>Закрыть</a>
                <h1>Другие страницы, зависимые от этой</h1>
                { data?.links?.length ? (
                    <>
                        <h2>Обратные ссылки</h2>
                        <ul>
                            { data.links.map((x, i) => (
                                <li key={i}>
                                    <a href={`/${x.id}`} className={x.exists?'':'newpage'}>{x.title||x.id} ({x.id})</a>
                                </li>
                            )) }
                        </ul>
                    </>
                ) : null }
                { data?.includes?.length ? (
                    <>
                        <h2>Включения (используя [[include]])</h2>
                        <ul>
                            { data.includes.map((x, i) => (
                                <li key={i}>
                                    <a href={`/${x.id}`} className={x.exists?'':'newpage'}>{x.title||x.id} ({x.id})</a>
                                </li>
                            )) }
                        </ul>
                    </>
                ) : null }
                { data?.children?.length ? (
                    <>
                        <h2>Дочерние страницы</h2>
                        <ul>
                            { data.children.map((x, i) => (
                                <li key={i}>
                                    <a href={`/${x.id}`} className={x.exists?'':'newpage'}>{x.title||x.id} ({x.id})</a>
                                </li>
                            )) }
                        </ul>
                    </>
                ) : null }
                { !data?.children?.length && !data?.links?.length && !data?.includes?.length && <p>На эту страницу нет обратных ссылок.</p> }
            </Styles>
        )
    }
}


export default ArticleBacklinksView