import * as React from 'react';
import { Component } from 'react';
import WikidotModal from "../util/wikidot-modal";
import styled from "styled-components";
import Loader from "../util/loader";
import {fetchPageVotes, ModuleRateVote, RatingMode} from "../api/rate";
import UserView from "../util/user-view";
import {sprintf} from 'sprintf-js'


interface Props {
    pageId: string
    rating: number
    onClose: () => void
}


interface State {
    loading: boolean
    rating: number
    mode: RatingMode
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
            mode: 'disabled',
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
            this.setState({ loading: false, error: null, votes: rating.votes, rating: rating.rating, mode: rating.mode });
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

    renderUserVote(vote) {
        const { mode } = this.state;
        if (mode === 'updown') {
            return vote > 0 ? '+' : '-';
        } else if (mode === 'stars') {
            return sprintf('%.1f', vote);
        } else {
            return null;
        }
    }

    renderUpDownRating() {
        const { pageId } = this.props;
        const { rating } = this.state;

        return (
            <div className="w-rate-module page-rate-widget-box" data-page-id={pageId}>
                <span className="rate-points">рейтинг:&nbsp;<span className="number prw54353">{rating>=0?`+${rating}`:rating}</span></span>
                <span className="rateup btn btn-default"><a title="Мне нравится" href="#">+</a></span>
                <span className="ratedown btn btn-default"><a title="Мне не нравится" href="#">-</a></span>
                <span className="cancel btn btn-default"><a title="Отменить голос" href="#">X</a></span>
            </div>
        )
    }

    renderStarsRating() {
        const { pageId } = this.props;
        const { rating, votes } = this.state;

        return (
            <div className="w-stars-rate-module" data-page-id={pageId}>
                <div className="w-stars-rate-rating">рейтинг:&nbsp;<span className="w-stars-rate-number">{votes.length ? sprintf('%.1f', rating) : '—'}</span></div>
                <div className="w-stars-rate-control">
                    <div className="w-stars-rate-stars-wrapper">
                        <div className="w-stars-rate-stars-view" style={{width: `${Math.floor(rating*20)}%`}} />
                    </div>
                    <div className="w-stars-rate-cancel" />
                </div>
                <div className="w-stars-rate-votes">голосов:&nbsp;<span className="w-stars-rate-number">{votes.length}</span></div>
            </div>
        )
    }

    renderRating() {
        const { mode } = this.state;

        if (mode === 'updown') {
            return this.renderUpDownRating();
        } else if (mode === 'stars') {
            return this.renderStarsRating();
        } else {
            return null;
        }
    }

    render() {
        const { error, loading, votes } = this.state;
        return (
            <Styles>
                { error && (
                    <WikidotModal buttons={[{title: 'Закрыть', onClick: this.onCloseError}]}>
                        <strong>Ошибка:</strong> {error}
                    </WikidotModal>
                ) }
                <a className="action-area-close btn btn-danger" href="#" onClick={this.onClose}>Закрыть</a>
                <h1>Рейтинг страницы</h1>
                <span>
                    Оценить страницу:<br/><br/>
                    {this.renderRating()}
                </span>
                <div id="who-rated-page-area" className={`${loading?'loading':''}`}>
                    { loading && <Loader className="loader" /> }
                    { !!(votes && votes.length) && <h2>Список голосовавших за страницу</h2>}
                    { votes.map((vote, i) => (
                        <React.Fragment key={i}>
                            <UserView data={vote.user} />&nbsp;{this.renderUserVote(vote.value)}<br/>
                        </React.Fragment>
                    )) }
                </div>
            </Styles>
        )
    }
}


export default ArticleRating