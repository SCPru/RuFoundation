import * as React from 'react';
import { Component } from 'react';
import {fetchArticle} from "../api/articles";
import WikidotModal from "../util/wikidot-modal";
import styled from "styled-components";
import Loader from "../util/loader";
import {fetchPageRating, fetchPageVotes, ModuleRateVote} from "../api/rate";
import UserView from "../util/user-view";


interface Props {
    pageId: string
    rating: number
    onClose: () => void
}


interface State {
    loading: boolean
    rating: number
    votes?: Array<ModuleRateVote>
    error?: string
}


const Styles = styled.div<{loading?: boolean}>`
#who-rated-page-area.loading {
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

`;


class ArticleRating extends Component<Props, State> {

    constructor(props) {
        super(props);
        this.state = {
            loading: false,
            votes: [],
            rating: props.rating
        };
    }

    componentDidMount() {
        this.loadRating();
    }

    async loadRating() {
        const { pageId } = this.props;
        this.setState({ loading: true, error: null });
        try {
            const rating = await fetchPageVotes(pageId);
            this.setState({ loading: false, error: null, votes: rating.votes, rating: rating.rating });
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
        const { pageId } = this.props;
        const { error, loading, rating, votes } = this.state;
        return (
            <Styles>
                { error && (
                    <WikidotModal buttons={[{title: 'Закрыть', onClick: this.onCloseError}]}>
                        <strong>Ошибка:</strong> {error}
                    </WikidotModal>
                ) }
                <a className="action-area-close btn btn-danger" href="#" onClick={this.onClose}>Закрыть</a>
                <h1>Рейтинг страницы</h1>
                <p>
                    Оценить страницу:
                    &nbsp;
                    &nbsp;
                    <div className="w-rate-module page-rate-widget-box" data-page-id={pageId}>
                        <span className="rate-points">рейтинг:&nbsp;<span className="number prw54353">{rating>=0?`+${rating}`:rating}</span></span>
                        <span className="rateup btn btn-default"><a title="Мне нравится" href="#">+</a></span>
                        <span className="ratedown btn btn-default"><a title="Мне не нравится" href="#">-</a></span>
                        <span className="cancel btn btn-default"><a title="Отменить голос" href="#">X</a></span>
                    </div>
                </p>
                <div id="who-rated-page-area" className={`${loading?'loading':''}`}>
                    { loading && <Loader className="loader" /> }
                    { votes && votes.length && <h2>Список голосовавших за страницу</h2>}
                    { votes.map((vote, i) => (
                        <React.Fragment key={i}>
                            <UserView data={vote.user} />&nbsp;{vote.value>0?'+':'-'}<br/>
                        </React.Fragment>
                    )) }
                </div>
            </Styles>
        )
    }
}


export default ArticleRating