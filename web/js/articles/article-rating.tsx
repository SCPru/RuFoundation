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
    popularity?: number
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
            this.setState({ loading: false, error: null, votes: rating.votes, rating: rating.rating, popularity: rating.popularity, mode: rating.mode });
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
        const { rating, votes, popularity } = this.state;

        return (
            <div className="w-stars-rate-module" data-page-id={pageId}>
                <div className="w-stars-rate-rating">рейтинг:&nbsp;<span className="w-stars-rate-number">{votes.length ? sprintf('%.1f', rating) : '—'}</span></div>
                <div className="w-stars-rate-control">
                    <div className="w-stars-rate-stars-wrapper">
                        <div className="w-stars-rate-stars-view" style={{width: `${Math.floor(rating*20)}%`}} />
                    </div>
                    <div className="w-stars-rate-cancel" />
                </div>
                <div className="w-stars-rate-votes"><span className="w-stars-rate-number" title="Количество голосов">{votes.length}</span>/<span className="w-stars-rate-popularity" title="Популярность (процент голосов 3.0 и выше)">{popularity}</span>%
                </div>
            </div>
        )
    }

    renderUpDownRatingDistribution() {
        const { votes } = this.state;

        let votesCount = [0, 0];

        votes?.forEach(vote => {
            if (vote.value > 0) votesCount[1] ++;
        })

        votesCount[0] = votes?.length - votesCount[1];

        const maxCount = Math.max(...votesCount);

        return (
            <div className="w-rate-dist">
                { !!(votesCount && votesCount.length) }
                { votesCount.map((stat, i) => (
                    <div className="w-rate-row">
                        <div className="w-rate-num">{ i ? '-' : '+' }</div>
                        <div className="w-rate-bar">
                            <div className="w-bar-fill" style={{ width: `${maxCount > 0 ? votesCount[1-i] * 100 / votes.length : 0}%` }}></div>
                        </div>
                        <div className="w-rate-stat">
                            <div className="w-v-count">{ maxCount > 0 ? votesCount[1-i] : '—' }</div>
                            <div>{ maxCount > 0 ? `${Math.round(votesCount[1-i] * 100 / votes.length)}%` : '—' }</div>
                        </div>
                    </div>
                )) }
            </div>
        )
    }

    renderStarsRatingDistribution() {
        const { votes } = this.state;

        let votesCount = [0, 0, 0, 0, 0, 0];
        let votesPercent = [0, 0, 0, 0, 0, 0];

        votes?.forEach(vote => {
            let minCount = Math.floor(vote.value);
            let affectMin = 1.0 - (vote.value - minCount);
            let affectMax = 1.0 - (minCount + 1.0 - vote.value);
            votesCount[minCount] += affectMin;
            if (minCount + 1 <= 5) {
                votesCount[minCount + 1] += affectMax;
            }
        })

        const maxCount = Math.max(...votesCount);

        return (
            <div className="w-rate-dist">
                { !!(votesCount && votesCount.length) }
                { votesCount.map((stat, i) => (
                    <div className="w-rate-row">
                        <div className="w-rate-num w-afterstar">{ 5 - i }</div>
                        <div className="w-rate-bar">
                            <div className="w-bar-fill" style={{ width: `${maxCount > 0 ? votesCount[5-i] * 100 / maxCount : '0'}%` }}></div>
                        </div>
                        <div className="w-rate-stat">
                            <div className="w-v-count">{ maxCount > 0 ? `${Math.round(votesCount[5-i] * 100 / votes.length)}%` : '—' }</div>
                        </div>
                    </div>
                )) }
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

    renderRatingDistribution() {
        const { mode } = this.state;

        if (mode === 'updown') {
            return this.renderUpDownRatingDistribution();
        } else if (mode === 'stars') {
            return this.renderStarsRatingDistribution();
        } else {
            return null;
        }
    }

    render() {
        const { error, loading, votes } = this.state;
        return (
            <Styles>
                { error && (
                    <WikidotModal buttons={[{title: 'Закрыть', onClick: this.onCloseError}]} isError>
                        <p><strong>Ошибка:</strong> {error}</p>
                    </WikidotModal>
                ) }
                <a className="action-area-close btn btn-danger" href="#" onClick={this.onClose}>Закрыть</a>
                <h1>Рейтинг страницы</h1>
                <span>
                    Оценить страницу:<br/><br/>
                    <div className="article-rating-widgets-area">
                        {this.renderRating()}
                        {this.renderRatingDistribution()}
                    </div>
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