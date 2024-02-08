import * as React from 'react';
import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer';
import { Component } from 'react';
import {ArticleLogEntry, fetchArticleVersion} from "../api/articles";
import WikidotModal from "../util/wikidot-modal";
import styled from "styled-components";
import Loader from "../util/loader";
import formatDate from "../util/date-format";


interface Props {
    pageId: string
    pathParams?: { [key: string]: string }
    onClose: () => void
    firstEntry: ArticleLogEntry
    secondEntry: ArticleLogEntry
}


interface State {
    loading: boolean
    firstSource?: string
    secondSource?: string
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


class ArticleDiffView extends Component<Props, State> {
    diffStyles = {
        variables: {
            light: {
                emptyLineBackground: ''
            }
        },
        wordDiff: {
            display: 'inline'
        },
        contentText: {
            fontFamily: 'inherit',
            color: '#242424'
        },
        lineNumber: {
            fontFamily: 'inherit'
        }
    }

    constructor(props) {
        super(props);
        this.state = {
            loading: false
        };
    }

    componentDidMount() {
        this.compareSource();
    }

    componentDidUpdate(prevProps: Readonly<Props>, prevState: Readonly<State>, snapshot?: any) {
        if (this.props.firstEntry !== prevProps.firstEntry || this.props.secondEntry !== prevProps.secondEntry) {
            this.compareSource();
        }
    }

    async compareSource() {
        const { pageId, firstEntry, secondEntry, pathParams } = this.props;

        this.setState({ loading: true, error: null });
        try {
            const first = await fetchArticleVersion(pageId, firstEntry.revNumber, pathParams);
            const second = await fetchArticleVersion(pageId, secondEntry.revNumber, pathParams);

            this.setState({ loading: false, error: null, firstSource: first.source, secondSource: second.source });
        } catch (e) {
            this.setState({ loading: false, error: e.error || 'Ошибка связи с сервером' });
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
        const { firstEntry, secondEntry } = this.props;
        const { error, loading, firstSource, secondSource } = this.state;

        return (
            <Styles>
                { error && (
                    <WikidotModal buttons={[{title: 'Закрыть', onClick: this.onCloseError}]} isError>
                        <p><strong>Ошибка:</strong> {error}</p>
                    </WikidotModal>
                ) }
                <a className="action-area-close btn btn-danger" href="#" onClick={this.onClose}>Закрыть</a>
                <h1>Сравнить ревизии страницы</h1>
                <div className="diff-box">
                    <table className="page-compare">
                        <tbody>
                        <tr>
                            <th></th>
                            <th>Правка {firstEntry.revNumber}</th>
                            <th>Правка {secondEntry.revNumber}</th>
                        </tr>
                        <tr>
                            <td>Создано:</td>
                            <td>{formatDate(new Date(firstEntry.createdAt))}</td>
                            <td>{formatDate(new Date(secondEntry.createdAt))}</td>
                        </tr>
                        </tbody>
                    </table>
                    <h3>Изменение источника:</h3>
                    { loading && <Loader className="loader" /> }
                    <ReactDiffViewer oldValue={firstSource} newValue={secondSource} compareMethod={DiffMethod.WORDS} splitView={false} styles={this.diffStyles} />
                </div>
            </Styles>
        )
    }
}


export default ArticleDiffView