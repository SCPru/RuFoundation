import * as React from 'react'
import { useEffect, useState } from 'react'
import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer'
import styled from 'styled-components'
import { ArticleLogEntry, fetchArticleVersion } from '../api/articles'
import useConstCallback from '../util/const-callback'
import formatDate from '../util/date-format'
import Loader from '../util/loader'
import WikidotModal from '../util/wikidot-modal'

interface Props {
  pageId: string
  pathParams?: { [key: string]: string }
  onClose: () => void
  firstEntry: ArticleLogEntry
  secondEntry: ArticleLogEntry
}

const Styles = styled.div<{ loading?: boolean }>`
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
`

const ArticleDiffView: React.FC<Props> = ({ pageId, pathParams, onClose: onCloseDelegate, firstEntry, secondEntry }) => {
  const [loading, setLoading] = useState(false)
  const [firstSource, setFirstSource] = useState('')
  const [secondSource, setSecondSource] = useState('')
  const [error, setError] = useState('')

  const diffStyles = {
    variables: {
      light: {
        emptyLineBackground: '',
      },
    },
    wordDiff: {
      display: 'inline',
    },
    contentText: {
      fontFamily: 'inherit',
      color: '#242424',
    },
    lineNumber: {
      fontFamily: 'inherit',
    },
  }

  useEffect(() => {
    compareSource()
  }, [])

  useEffect(() => {
    compareSource()
  }, [firstEntry, secondEntry])

  const compareSource = useConstCallback(async () => {
    setLoading(true)
    setError(undefined)

    try {
      const first = await fetchArticleVersion(pageId, firstEntry.revNumber, pathParams)
      const second = await fetchArticleVersion(pageId, secondEntry.revNumber, pathParams)

      setFirstSource(first.source)
      setSecondSource(second.source)
    } catch (e) {
      setError(e.error || 'Ошибка связи с сервером')
    } finally {
      setLoading(false)
    }
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
    onClose(null)
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
      <a className="action-area-close btn btn-danger" href="#" onClick={onClose}>
        Закрыть
      </a>
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
        {loading && <Loader className="loader" />}
        <ReactDiffViewer oldValue={firstSource} newValue={secondSource} compareMethod={DiffMethod.WORDS} splitView={false} styles={diffStyles} />
      </div>
    </Styles>
  )
}

export default ArticleDiffView
