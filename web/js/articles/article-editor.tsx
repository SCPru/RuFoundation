import * as React from 'react'
import { useEffect, useState } from 'react'
import styled from 'styled-components'
import { createArticle, fetchArticle, updateArticle } from '../api/articles'
import { makePreview } from '../api/preview'
import useConstCallback from '../util/const-callback'
import Loader from '../util/loader'
import { removeMessage, showPreviewMessage } from '../util/wikidot-message'
import WikidotModal from '../util/wikidot-modal'

interface Props {
  pageId: string
  pathParams?: { [key: string]: string }
  isNew?: boolean
  onClose?: () => void
  previewTitleElement?: HTMLElement | (() => HTMLElement)
  previewBodyElement?: HTMLElement | (() => HTMLElement)
  previewStyleElement?: HTMLElement | (() => HTMLElement)
}

interface State {
  title: string
  source: string
  comment: string
  loading: boolean
  saving: boolean
  savingSuccess?: boolean
  error?: string
  fatalError?: boolean
  saved?: boolean
  previewOriginalTitle?: string
  previewOriginalTitleDisplay?: string
  previewOriginalBody?: string
}

function guessTitle(pageId: string) {
  const pageIdSplit = pageId.split(':', 2)
  if (pageIdSplit.length === 2) pageId = pageIdSplit[1]
  else pageId = pageIdSplit[0]

  let result = ''
  let brk = true
  for (let i = 0; i < pageId.length; i++) {
    let char = pageId[i]
    if (char === '-') {
      if (!brk) {
        result += ' '
      }
      brk = true
      continue
    }
    if (brk) {
      char = char.toUpperCase()
      brk = false
    } else {
      char = char.toLowerCase()
    }
    result += char
  }
  return result
}

function getElement(e: HTMLElement | (() => HTMLElement)) {
  if (typeof e === 'function') {
    return e()
  }
  return e
}

const Styles = styled.div`
  .editor-area {
    position: relative;

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
`

const ArticleEditor: React.FC<Props> = ({ pageId, pathParams, isNew, onClose, previewTitleElement, previewBodyElement, previewStyleElement }) => {
  const [title, setTitle] = useState('')
  const [source, setSource] = useState('')
  const [comment, setComment] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [savingSuccess, setSavingSuccess] = useState(false)
  const [error, setError] = useState(false)
  const [fatalError, setFatalError] = useState(false)
  const [saved, setSaved] = useState(false)
  const [previewOriginalTitle, setPreviewOriginalTitle] = useState('')
  const [previewOriginalTitleDisplay, setPreviewOriginalTitleDisplay] = useState('')
  const [previewOriginalBody, setPreviewOriginalBody] = useState('')
  const [previewOriginalStyle, setPreviewOriginalStyle] = useState('')

  useEffect(() => {
    setTitle(isNew ? guessTitle(pageId) : '')
    setPreviewOriginalTitle(getElement(previewTitleElement)?.innerText)
    setPreviewOriginalTitleDisplay(getElement(previewTitleElement)?.style?.display)
    setPreviewOriginalBody(getElement(previewBodyElement)?.innerHTML)
    setPreviewOriginalStyle(getElement(previewStyleElement)?.innerHTML)

    window.addEventListener('beforeunload', handleRefresh)

    if (!isNew) {
      setLoading(true)
      fetchArticle(pageId)
        .then(data => {
          setSource(data.source)
          setTitle(data.title)
        })
        .catch(e => {
          setFatalError(true)
          setError(e.error || 'Ошибка связи с сервером')
        })
        .finally(() => {
          setLoading(false)
        })
    }

    return () => {
      window.removeEventListener('beforeunload', handleRefresh)
    }
  }, [])

  const handleRefresh = useConstCallback(event => {
    if (!saved) {
      event.preventDefault()
      event.returnValue = ''
    }
  })

  const onSubmit = useConstCallback(() => {
    setSaving(true)
    setError(undefined)
    setSavingSuccess(false)

    const input = {
      pageId: pageId,
      title: title,
      source: source,
      comment: comment,
      parent: pathParams['parent'],
    }

    if (isNew) {
      createArticle(input)
        .then(() => {
          setSavingSuccess(true)
          setSaved(true)
          setTimeout(() => {
            setSavingSuccess(false)
            window.location.href = `/${pageId}`
          }, 1000)
        })
        .catch(e => {
          setSaved(false)
          setFatalError(false)
          setError(e.error || 'Ошибка связи с сервером')
        })
        .finally(() => {
          setSaving(false)
        })
    } else {
      updateArticle(pageId, input)
        .then(() => {
          setSavingSuccess(true)
          setSaved(true)
          setTimeout(() => {
            setSavingSuccess(false)
            window.scrollTo(window.scrollX, 0)
            if (pathParams['edit']) {
              window.location.href = `/${pageId}`
            } else {
              window.location.reload()
            }
          }, 1000)
        })
        .catch(e => {
          setSavingSuccess(false)
          setFatalError(false)
          setSaved(false)
          setError(e.error || 'Ошибка связи с сервером')
        })
        .finally(() => {
          setSaving(false)
        })
    }
  })

  const onPreview = useConstCallback(() => {
    const data = {
      pageId: pageId,
      title: title,
      source: source,
      pathParams: pathParams,
    }

    makePreview(data).then(function (resp) {
      showPreviewMessage()
      getElement(previewTitleElement).innerText = resp.title
      getElement(previewTitleElement).style.display = ''
      getElement(previewBodyElement).innerHTML = resp.content
      getElement(previewStyleElement).innerHTML = resp.style
    })
  })

  const onCancel = useConstCallback(e => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    removeMessage()
    if (typeof previewOriginalTitle === 'string') {
      getElement(previewTitleElement).innerText = previewOriginalTitle
      getElement(previewTitleElement).style.display = previewOriginalTitleDisplay
    }
    if (typeof previewOriginalBody === 'string') {
      getElement(previewBodyElement).innerHTML = previewOriginalBody
    }
    if (typeof previewOriginalStyle === 'string') {
      getElement(previewStyleElement).innerHTML = previewOriginalStyle
    }
    if (onClose) onClose()
  })

  const onChange = useConstCallback(e => {
    setSaved(false)
    switch (e.target.name) {
      case 'title':
        setTitle(e.target.value)
        break
      case 'source':
        setSource(e.target.value)
        break
      case 'comment':
        setComment(e.target.value)
        break
    }
  })

  const onCloseError = useConstCallback(() => {
    setError(undefined)
    if (fatalError) {
      onCancel(null)
    }
  })

  return (
    <Styles>
      {saving && (
        <WikidotModal isLoading>
          <p>Сохранение...</p>
        </WikidotModal>
      )}
      {savingSuccess && (
        <WikidotModal>
          <p>Успешно сохранено!</p>
        </WikidotModal>
      )}
      {error && (
        <WikidotModal buttons={[{ title: 'Закрыть', onClick: onCloseError }]} isError>
          <p>
            <strong>Ошибка:</strong> {error}
          </p>
        </WikidotModal>
      )}
      {isNew ? <h1>Создать страницу</h1> : <h1>Редактировать страницу</h1>}
      <form id="edit-page-form" onSubmit={onSubmit}>
        <table className="form" style={{ margin: '0.5em auto 1em 0' }}>
          <tbody>
            <tr>
              <td>Заголовок страницы:</td>
              <td>
                <input
                  id="edit-page-title"
                  value={title}
                  onChange={onChange}
                  name="title"
                  type="text"
                  size={35}
                  maxLength={128}
                  style={{ fontWeight: 'bold', fontSize: '130%' }}
                  disabled={loading || saving}
                />
              </td>
            </tr>
          </tbody>
        </table>
        {/* This is not supported right now but we have to add empty div for BHL */}
        <div id="wd-editor-toolbar-panel" className="wd-editor-toolbar-panel" />
        <div className={`editor-area ${loading ? 'loading' : ''}`}>
          <textarea
            id="edit-page-textarea"
            value={source}
            onChange={onChange}
            name="source"
            rows={20}
            cols={60}
            style={{ width: '95%' }}
            disabled={loading || saving}
          />
          <p>Краткое описание изменений:</p>
          <textarea
            id="edit-page-comments"
            value={comment}
            onChange={onChange}
            name="comment"
            rows={3}
            cols={20}
            style={{ width: '35%' }}
            disabled={loading || saving}
          />
          {loading && <Loader className="loader" />}
        </div>
        <div className="buttons alignleft">
          <input
            id="edit-cancel-button"
            className="btn btn-danger"
            type="button"
            name="cancel"
            value="Отмена"
            onClick={onCancel}
            disabled={loading || saving}
          />
          <input
            id="edit-preview-button"
            className="btn btn-primary"
            type="button"
            name="preview"
            value="Предпросмотр"
            onClick={onPreview}
            disabled={loading || saving}
          />
          <input
            id="edit-save-button"
            className="btn btn-primary"
            type="button"
            name="save"
            value="Сохранить"
            onClick={onSubmit}
            disabled={loading || saving}
          />
        </div>
      </form>
    </Styles>
  )
}

export default ArticleEditor
