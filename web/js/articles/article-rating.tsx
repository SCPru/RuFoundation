import * as React from 'react'
import { useEffect, useState } from 'react'
import { sprintf } from 'sprintf-js'
import styled from 'styled-components'
import { deleteArticleVotes } from '../api/articles'
import { fetchPageVotes, ModuleRateVote, RatingMode } from '../api/rate'
import useConstCallback from '../util/const-callback'
import formatDate from '../util/date-format'
import Loader from '../util/loader'
import UserView from '../util/user-view'
import WikidotModal from '../util/wikidot-modal'

interface Props {
  pageId: string
  rating: number
  canEdit: boolean
  onClose: () => void
}

const Styles = styled.div<{ loading?: boolean }>`
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
  .admin-vote-date {
    font-size: 90%;
    font-style: italic;
    opacity: 0.5;
  }
  .w-rating-clear-rating-button {
    width: 100%;
  }
  .article-rating-widgets-area {
    display: flex;
    flex-wrap: wrap;
    column-gap: 25px;
  }
  .w-rate-dist {
    font-family: sans-serif;
    overflow-wrap: normal;
    font-weight: bold;
    max-width: 100%;
  }
  .w-rate-row {
    display: grid;
    align-items: center;
    grid-template-columns: max-content max-content max-content;
  }
  .w-rate-bar {
    width: 236px;
    height: 10px;
    border-radius: 5px;
    background-color: #eee;
  }
  .w-bar-fill {
    height: 100%;
    border-radius: inherit;
    background-color: #4e6b6b;
  }
  .w-rate-num {
    width: 25px;
  }
  .w-rate-stat {
    display: grid;
    grid-template-columns: auto auto;
  }
  .w-v-count {
    padding: 0 5px;
    width: 25px;
  }
  .w-afterstar {
    &:after {
      font-family: 'Font Awesome 5 Free';
      content: '\f005';
      font-weight: 600;
      color: #f0ac00;
    }
  }
`

const ArticleRating: React.FC<Props> = ({ pageId, rating: originalRating, canEdit, onClose: onCloseDelegate }) => {
  const [loading, setLoading] = useState(false)
  const [rating, setRating] = useState(originalRating)
  const [mode, setMode] = useState<RatingMode>('disabled')
  const [votes, setVotes] = useState<Array<ModuleRateVote>>([])
  const [popularity, setPopularity] = useState(0)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    window.addEventListener('message', onRatingUpdated)
    loadRating()

    return () => {
      window.removeEventListener('message', onRatingUpdated)
    }
  }, [])

  const loadRating = useConstCallback(async () => {
    setLoading(true)
    setError(undefined)
    try {
      const rating = await fetchPageVotes(pageId)
      setVotes(rating.votes)
      setRating(rating.rating)
      setPopularity(rating.popularity)
      setMode(rating.mode)
    } catch (e) {
      setError(e.error || 'Ошибка связи с сервером')
    } finally {
      setLoading(false)
    }
  })

  const onRatingUpdated = useConstCallback((message: MessageEvent) => {
    if (message.data?.type !== 'rate_updated') {
      return
    }
    loadRating()
  })

  const onClearRating = useConstCallback(async () => {
    setLoading(true)
    setError(undefined)
    setDeleting(false)
    try {
      const rating = await deleteArticleVotes(pageId)
      setVotes(rating.votes)
      setRating(rating.rating)
      setPopularity(rating.popularity)
      setMode(rating.mode)
    } catch (e) {
      setError(e.error || 'Ошибка связи с сервером')
    } finally {
      setLoading(false)
    }
  })

  const onAskClearRating = useConstCallback(() => {
    setDeleting(true)
  })

  const onCancelClearRating = () => {
    setDeleting(false)
  }

  const onClose = useConstCallback(e => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    if (onCloseDelegate) onCloseDelegate()
  })

  const onCloseError = useConstCallback(() => {
    setError(undefined)
    onClose(null)
  })

  const renderUserVote = useConstCallback(vote => {
    if (mode === 'updown') {
      return vote > 0 ? '+' : '-'
    } else if (mode === 'stars') {
      return sprintf('%.1f', vote)
    } else {
      return null
    }
  })

  const renderUpDownRating = useConstCallback(() => {
    return (
      <div className="w-rate-module page-rate-widget-box" data-page-id={pageId}>
        <span className="rate-points">
          рейтинг:&nbsp;<span className="number prw54353">{rating >= 0 ? `+${rating}` : rating}</span>
        </span>
        <span className="rateup btn btn-default">
          <a title="Мне нравится" href="#">
            +
          </a>
        </span>
        <span className="ratedown btn btn-default">
          <a title="Мне не нравится" href="#">
            -
          </a>
        </span>
        <span className="cancel btn btn-default">
          <a title="Отменить голос" href="#">
            X
          </a>
        </span>
      </div>
    )
  })

  const renderStarsRating = useConstCallback(() => {
    return (
      <div className="w-stars-rate-module" data-page-id={pageId}>
        <div className="w-stars-rate-rating">
          рейтинг:&nbsp;<span className="w-stars-rate-number">{votes.length ? sprintf('%.1f', rating) : '—'}</span>
        </div>
        <div className="w-stars-rate-control">
          <div className="w-stars-rate-stars-wrapper">
            <div className="w-stars-rate-stars-view" style={{ width: `${Math.floor(rating * 20)}%` }} />
          </div>
          <div className="w-stars-rate-cancel" />
        </div>
        <div className="w-stars-rate-votes">
          <span className="w-stars-rate-number" title="Количество голосов">
            {votes.length}
          </span>
          /
          <span className="w-stars-rate-popularity" title="Популярность (процент голосов 3.0 и выше)">
            {popularity}
          </span>
          %
        </div>
      </div>
    )
  })

  const renderUpDownRatingDistribution = useConstCallback(() => {
    let votesCount = [0, 0]

    votes?.forEach(vote => {
      if (vote.value > 0) votesCount[1]++
    })

    votesCount[0] = votes?.length - votesCount[1]

    const maxCount = Math.max(...votesCount)

    return (
      <div className="w-rate-dist">
        {!!(votesCount && votesCount.length)}
        {votesCount.map((stat, i) => (
          <div className="w-rate-row">
            <div className="w-rate-num">{i ? '-' : '+'}</div>
            <div className="w-rate-bar">
              <div className="w-bar-fill" style={{ width: `${maxCount > 0 ? (votesCount[1 - i] * 100) / votes.length : 0}%` }}></div>
            </div>
            <div className="w-rate-stat">
              <div className="w-v-count">{maxCount > 0 ? votesCount[1 - i] : '—'}</div>
              <div>{maxCount > 0 ? `${Math.round((votesCount[1 - i] * 100) / votes.length)}%` : '—'}</div>
            </div>
          </div>
        ))}
      </div>
    )
  })

  const renderStarsRatingDistribution = useConstCallback(() => {
    let votesCount = [0, 0, 0, 0, 0, 0]

    votes?.forEach(vote => {
      let minCount = Math.floor(vote.value)
      let affectMin = 1.0 - (vote.value - minCount)
      let affectMax = 1.0 - (minCount + 1.0 - vote.value)
      votesCount[minCount] += affectMin
      if (minCount + 1 <= 5) {
        votesCount[minCount + 1] += affectMax
      }
    })

    const maxCount = Math.max(...votesCount)

    return (
      <div className="w-rate-dist">
        {!!(votesCount && votesCount.length)}
        {votesCount.map((stat, i) => (
          <div className="w-rate-row" key={i}>
            <div className="w-rate-num w-afterstar">{5 - i}</div>
            <div className="w-rate-bar">
              <div className="w-bar-fill" style={{ width: `${maxCount > 0 ? (votesCount[5 - i] * 100) / maxCount : '0'}%` }}></div>
            </div>
            <div className="w-rate-stat">
              <div className="w-v-count">{maxCount > 0 ? `${Math.round((votesCount[5 - i] * 100) / votes.length)}%` : '—'}</div>
            </div>
          </div>
        ))}
      </div>
    )
  })

  const renderRating = useConstCallback(() => {
    let ratingElement: React.ReactNode

    if (mode === 'updown') {
      ratingElement = renderUpDownRating()
    } else if (mode === 'stars') {
      ratingElement = renderStarsRating()
    } else {
      return null
    }

    if (!ratingElement) {
      return null
    }

    return (
      <div>
        {ratingElement}
        {canEdit && (
          <>
            <br />
            <button className="w-rating-clear-rating-button" onClick={onAskClearRating}>
              Сбросить рейтинг
            </button>
          </>
        )}
      </div>
    )
  })

  const renderRatingDistribution = useConstCallback(() => {
    if (mode === 'updown') {
      return renderUpDownRatingDistribution()
    } else if (mode === 'stars') {
      return renderStarsRatingDistribution()
    } else {
      return null
    }
  })

  const renderVoteDate = useConstCallback((date?: string) => {
    if (!date) {
      return null
    }

    return (
      <>
        &nbsp;
        <span className="admin-vote-date">({formatDate(new Date(date))})</span>
      </>
    )
  })

  const sortVotes = useConstCallback((votes: ModuleRateVote[]) => {
    const groups: Array<{ name: string; index: number; votes: ModuleRateVote[]; isUngrouped: boolean }> = []
    votes.forEach(vote => {
      if (vote.visualGroup) {
        const existingGroup = groups.find(x => x.name === vote.visualGroup)
        if (!existingGroup) {
          groups.push({
            name: vote.visualGroup,
            index: vote.visualGroupIndex || 0,
            votes: [vote],
            isUngrouped: false,
          })
        } else {
          existingGroup.votes.push(vote)
        }
      }
    })
    groups.sort((a, b) => {
      if (a.index < b.index) return -1
      if (a.index > b.index) return 1
      return a.name.localeCompare(b.name)
    })
    const editorVotes = votes.filter(x => !x.visualGroup && x.user.editor)
    const readerVotes = votes.filter(x => !x.visualGroup && !x.user.editor)
    if (editorVotes.length) {
      groups.push({
        name: 'Голоса участников',
        index: -1,
        votes: editorVotes,
        isUngrouped: true,
      })
    }
    if (readerVotes.length) {
      groups.push({
        name: 'Голоса читателей',
        index: -1,
        votes: readerVotes,
        isUngrouped: true,
      })
    }
    return groups
  })

  const renderCombinedVoteRating = useConstCallback((votes: ModuleRateVote[]) => {
    if (mode === 'updown') {
      return votes.reduce((acc, vote) => (acc + vote.value > 0 ? 1 : -1), 0)
    } else if (mode === 'stars') {
      const votesCount = votes.length
      const votesTotal = votes.reduce((acc, vote) => acc + vote.value, 0)
      if (!votesCount) {
        return '—'
      }
      return sprintf('%.1f', votesTotal / votesCount)
    } else {
      return '—'
    }
  })

  return (
    <Styles>
      {error && (
        <WikidotModal buttons={[{ title: 'Закрыть', onClick: onCloseError }]} isError>
          <p>
            <strong>Ошибка:</strong> {error}
          </p>
        </WikidotModal>
      )}
      {deleting && (
        <WikidotModal
          buttons={[
            { title: 'Отмена', onClick: onCancelClearRating },
            { title: 'Да, сбросить', onClick: onClearRating },
          ]}
        >
          <h1>Сбросить рейтинг страницы?</h1>
          <p>Обратите внимание, что данную операцию можно будет откатить через историю правок.</p>
        </WikidotModal>
      )}
      <a className="action-area-close btn btn-danger" href="#" onClick={onClose}>
        Закрыть
      </a>
      <h1>Рейтинг страницы</h1>
      <span>
        Оценить страницу:
        <br />
        <br />
        <div className="article-rating-widgets-area">
          {renderRating()}
          {renderRatingDistribution()}
        </div>
      </span>
      <div id="who-rated-page-area" className={`${loading ? 'loading' : ''}`}>
        {loading && <Loader className="loader" />}
        {sortVotes(votes).map((group, i) => (
          <React.Fragment key={i}>
            <h2>
              {group.name} ({renderCombinedVoteRating(group.votes)})
            </h2>
            {group.votes.map((vote, i) => (
              <React.Fragment key={i}>
                <UserView data={vote.user} />
                &nbsp;{renderUserVote(vote.value)}
                {renderVoteDate(vote.date)}
                <br />
              </React.Fragment>
            ))}
          </React.Fragment>
        ))}
      </div>
    </Styles>
  )
}

export default ArticleRating
