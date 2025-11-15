import * as React from 'react'
import { useEffect, useState } from 'react'
import { sprintf } from 'sprintf-js'
import styled from 'styled-components'
import { ArticleLogEntry, fetchArticleLog, fetchArticleVersion } from '../api/articles'
import useConstCallback from '../util/const-callback'
import formatDate from '../util/date-format'
import Loader from '../util/loader'
import Pagination from '../util/pagination'
import UserView from '../util/user-view'
import { showVersionMessage } from '../util/wikidot-message'
import WikidotModal, { showRevertModal } from '../util/wikidot-modal'
import ArticleDiffView from './article-diff'
import ArticleSource from './article-source'

interface Props {
  pageId: string
  pathParams?: { [key: string]: string }
  onClose: () => void
}

const Styles = styled.div<{ loading?: boolean }>`
  #revision-list.loading {
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
  .page-history {
    tr td {
      &:nth-child(2) {
        width: 5em;
      }
      &:nth-child(4) {
        width: 5em;
      }
      &:nth-child(5) {
        width: 15em;
      }
      &:nth-child(6) {
        padding: 0 0.5em;
        width: 12em;
      }
      &:nth-child(7) {
        font-size: 90%;
      }
      .action {
        border: 1px solid #bbb;
        padding: 0 3px;
        text-decoration: none;
        color: #824;
        background: transparent;
        cursor: pointer;
      }
    }
  }
`

export function renderArticleHistoryFlags(entry: ArticleLogEntry) {
  const renderType = type => {
    switch (type) {
      case 'new':
        return (
          <span className="spantip" title="создана новая страница">
            N
          </span>
        )

      case 'title':
        return (
          <span className="spantip" title="изменился заголовок">
            T
          </span>
        )

      case 'source':
        return (
          <span className="spantip" title="изменился текст статьи">
            S
          </span>
        )

      case 'tags':
        return (
          <span className="spantip" title="метки изменились">
            A
          </span>
        )

      case 'name':
        return (
          <span className="spantip" title="страница переименована/удалена">
            R
          </span>
        )

      case 'parent':
        return (
          <span className="spantip" title="изменилась родительская страница">
            M
          </span>
        )

      case 'file_added':
        return (
          <span className="spantip" title="файл добавлен">
            F
          </span>
        )

      case 'file_deleted':
        return (
          <span className="spantip" title="файл удалён">
            F
          </span>
        )

      case 'file_renamed':
        return (
          <span className="spantip" title="файл переименован">
            F
          </span>
        )

      case 'votes_deleted':
        return (
          <span className="spantip" title="голоса изменены">
            V
          </span>
        )

      case 'wikidot':
        return (
          <span className="spantip" title="правка, портированная с Wikidot">
            W
          </span>
        )
    }
  }

  if (entry.meta.subtypes) {
    return entry.meta.subtypes.map(x => <React.Fragment key={x}>{renderType(x)}</React.Fragment>)
  } else {
    return renderType(entry.type)
  }
}

export function renderArticleHistoryComment(entry: ArticleLogEntry) {
  if (entry.comment.trim()) {
    return entry.comment
  }
  return entry.defaultComment
  
  switch (entry.type) {
    case 'new':
      return 'Создание новой страницы'

    case 'title':
      return (
        <>
          Заголовок изменён с "<em>{entry.meta.prev_title}</em>" на "<em>{entry.meta.title}</em>"
        </>
      )

    case 'name':
      return (
        <>
          Страница переименована из "<em>{entry.meta.prev_name}</em>" в "<em>{entry.meta.name}</em>"
        </>
      )

    case 'tags':
      let added_tags = entry.meta.added_tags.map(tag => tag['name'])
      let removed_tags = entry.meta.removed_tags.map(tag => tag['name'])
      if (Array.isArray(added_tags) && added_tags.length && Array.isArray(removed_tags) && removed_tags.length) {
        return (
          <>
            Добавлены теги: {added_tags.join(', ')}. Удалены теги: {removed_tags.join(', ')}.
          </>
        )
      } else if (Array.isArray(added_tags) && added_tags.length) {
        return <>Добавлены теги: {added_tags.join(', ')}.</>
      } else if (Array.isArray(removed_tags) && removed_tags.length) {
        return <>Удалены теги: {removed_tags.join(', ')}.</>
      }
      break

    case 'parent':
      if (entry.meta.prev_parent && entry.meta.parent) {
        return (
          <>
            Родительская страница изменена с "<em>{entry.meta.prev_parent}</em>" на "<em>{entry.meta.parent}</em>"
          </>
        )
      } else if (entry.meta.prev_parent) {
        return (
          <>
            Убрана родительская страница "<em>{entry.meta.prev_parent}</em>"
          </>
        )
      } else if (entry.meta.parent) {
        return (
          <>
            Установлена родительская страница "<em>{entry.meta.parent}</em>"
          </>
        )
      }
      break

    case 'file_added':
      return (
        <>
          Загружен файл: "<em>{entry.meta.name}</em>"
        </>
      )

    case 'file_deleted':
      return (
        <>
          Удалён файл: "<em>{entry.meta.name}</em>"
        </>
      )

    case 'file_renamed':
      return (
        <>
          Переименован файл: "<em>{entry.meta.prev_name}</em>" в "<em>{entry.meta.name}</em>"
        </>
      )

    case 'votes_deleted': {
      let ratingStr = 'n/a'
      if (entry.meta.rating_mode === 'updown') {
        ratingStr = sprintf('%+d', entry.meta.rating)
      } else if (entry.meta.rating_mode === 'stars') {
        ratingStr = sprintf('%.1f', entry.meta.rating)
      }
      return (
        <>
          Сброшен рейтинг страницы: {ratingStr} (голосов: {entry.meta.votes_count}, популярность: {entry.meta.popularity}%)
        </>
      )
    }

    case 'authorship':{
      let added_authors = entry.meta.added_authors
      let removed_authors = entry.meta.removed_authors
      if (Array.isArray(added_authors) && added_authors.length && Array.isArray(removed_authors) && removed_authors.length) {
        return (
          <>
            Добавлены авторы: {added_authors.join(', ')}. Удалены авторы: {removed_authors.join(', ')}.
          </>
        )
      } else if (Array.isArray(added_authors) && added_authors.length) {
        return <>Добавлены авторы: {added_authors.join(', ')}.</>
      } else if (Array.isArray(removed_authors) && removed_authors.length) {
        return <>Удалены авторы: {removed_authors.join(', ')}.</>
      }
    }

    case 'revert':
      return <>Откат страницы к версии №{entry.meta.rev_number}</>
  }
}

const ArticleHistory: React.FC<Props> = ({ pageId, pathParams, onClose: onCloseDelegate }) => {
  const [loading, setLoading] = useState(false)
  const [entries, setEntries] = useState<Array<ArticleLogEntry>>([])
  const [subarea, setSubarea] = useState<JSX.Element>()
  const [entryCount, setEntryCount] = useState(0)
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(25)
  const [error, setError] = useState(0)
  const [fatalError, setFatalError] = useState(false)
  const [firstCompareEntry, setFirstCompareEntry] = useState<ArticleLogEntry>()
  const [secondCompareEntry, setSecondCompareEntry] = useState<ArticleLogEntry>()

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = useConstCallback(async (nextPage?: number) => {
    setLoading(true)
    setError(undefined)

    const realPage = nextPage || page
    const from = (realPage - 1) * perPage
    const to = realPage * perPage

    fetchArticleLog(pageId, from, to)
      .then(history => {
        setEntries(history.entries)
        setEntryCount(history.count)
        setPage(realPage)
        setFirstCompareEntry(history.entries[1])
        setSecondCompareEntry(history.entries[0])
      })
      .catch(e => {
        setFatalError(entries === null)
        setError(e.error || 'Ошибка связи с сервером')
      })
      .finally(() => {
        setLoading(false)
      })
  })

  const onClose = useConstCallback(e => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    if (onCloseDelegate) onCloseDelegate()
  })

  const onCloseError = useConstCallback(() => {
    setError(undefined)
    if (fatalError) {
      onClose(null)
    }
  })

  const onChangePage = useConstCallback(nextPage => {
    loadHistory(nextPage)
  })

  const renderActions = useConstCallback((entry: ArticleLogEntry) => {
    if (entry.type === 'wikidot') {
      return null
    }
    return (
      <>
        <a href="#" onClick={e => displayArticleVersion(e, entry)} title="Просмотр изменений страницы">
          V
        </a>
        <a href="#" onClick={e => displayVersionSource(e, entry)} title="Просмотр источника изменений">
          S
        </a>
        {entryCount !== entry.revNumber + 1 && (
          <a href="#" onClick={e => revertArticleVersion(e, entry)} title="Вернуться к правке">
            R
          </a>
        )}
      </>
    )
  })

  const renderUser = useConstCallback((entry: ArticleLogEntry) => {
    return <UserView data={entry.user} />
  })

  const renderDate = useConstCallback((entry: ArticleLogEntry) => {
    return formatDate(new Date(entry.createdAt))
  })

  const displayArticleVersion = useConstCallback((e: React.MouseEvent, entry: ArticleLogEntry) => {
    e.preventDefault()
    e.stopPropagation()

    fetchArticleVersion(pageId, entry.revNumber, pathParams).then(function (resp) {
      showVersionMessage(entry.revNumber, new Date(entry.createdAt), entry.user, pageId)
      document.getElementById('page-content').innerHTML = resp.rendered
    })
  })

  const displayVersionSource = useConstCallback((e: React.MouseEvent, entry: ArticleLogEntry) => {
    e.preventDefault()
    e.stopPropagation()

    fetchArticleVersion(pageId, entry.revNumber, pathParams).then(function (resp) {
      hideSubArea()
      showSubArea(<ArticleSource pageId={pageId} onClose={hideSubArea} source={resp.source} />)
    })
  })

  const displayVersionDiff = useConstCallback((e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()

    if (firstCompareEntry && secondCompareEntry) {
      hideSubArea()
      showSubArea(
        <ArticleDiffView
          pageId={pageId}
          onClose={hideSubArea}
          firstEntry={firstCompareEntry}
          secondEntry={secondCompareEntry}
          pathParams={pathParams}
        />,
      )
    }
  })

  const showSubArea = useConstCallback((component: JSX.Element) => {
    setSubarea(component)
  })

  const hideSubArea = useConstCallback(() => {
    setSubarea(undefined)
  })

  const revertArticleVersion = useConstCallback((e: React.MouseEvent, entry: ArticleLogEntry) => {
    e.preventDefault()
    e.stopPropagation()

    showRevertModal(pageId, entry)
  })

  const totalPages = Math.ceil(entryCount / perPage)

  return (
    <Styles>
      {error && (
        <WikidotModal buttons={[{ title: 'Закрыть', onClick: onCloseError }]} isError>
          <p>
            <strong>Ошибка:</strong> {error}
          </p>
        </WikidotModal>
      )}
      <a className="action-area-close btn btn-danger" href="#" onClick={onClose}>
        Закрыть
      </a>
      <h1>История изменений</h1>
      <div id="revision-list" className={`${loading ? 'loading' : ''}`}>
        {loading && <Loader className="loader" />}
        <div className="buttons">
          <input type="button" className="btn btn-default btn-sm" value="Обновить список" onClick={() => loadHistory()} />
          <input
            type="button"
            className="btn btn-default btn-sm"
            value="Сравнить редакции"
            name="compare"
            id="history-compare-button"
            onClick={displayVersionDiff}
          />
        </div>
        {entries && totalPages > 1 && <Pagination page={page} maxPages={totalPages} onChange={onChangePage} />}
        {entries && (
          <table className="page-history">
            <tbody>
              <tr>
                <td>рев.</td>
                <td>&nbsp;</td>
                <td>флаги</td>
                <td>действия</td>
                <td>от</td>
                <td>дата</td>
                <td>комментарии</td>
              </tr>
              {entries.map(entry => {
                return (
                  <tr key={entry.revNumber} id={`revision-row-${entry.revNumber}`}>
                    {/* BHL has CSS selector that says tr[id*="evision-row"] */}
                    <td>{entry.revNumber}.</td>
                    <td style={{ width: '5em' }}>
                      <input
                        type="radio"
                        name="from"
                        value={entry.revNumber}
                        onChange={() => {
                          setFirstCompareEntry(entry)
                        }}
                        defaultChecked={entries[1] === entry}
                      />
                      <input
                        type="radio"
                        name="to"
                        value={entry.revNumber}
                        onChange={() => {
                          setSecondCompareEntry(entry)
                        }}
                        defaultChecked={entries[0] === entry}
                      />
                    </td>
                    <td>{renderArticleHistoryFlags(entry)}</td>
                    <td className="optionstd" style={{ width: '5em' }}>
                      {renderActions(entry)}
                    </td>
                    <td style={{ width: '15em' }}>{renderUser(entry)}</td>
                    <td style={{ padding: '0 0.5em', width: '7em' }}>{renderDate(entry)}</td>
                    <td style={{ fontSize: '90%' }}>{renderArticleHistoryComment(entry)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
      <div id="history-subarea">{subarea}</div>
    </Styles>
  )
}

export default ArticleHistory
