import * as React from 'react'
import { useEffect, useState } from 'react'
import styled from 'styled-components'
import { fetchArticle, updateArticle } from '../api/articles'
import sleep from '../util/async-sleep'
import useConstCallback from '../util/const-callback'
import WikidotModal from '../util/wikidot-modal'

interface Props {
  pageId: string
  isNew?: boolean
  onClose?: () => void
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
`

const ArticleRename: React.FC<Props> = ({ pageId, isNew, onClose }) => {
  const [newName, setNewName] = useState(pageId)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [savingSuccess, setSavingSuccess] = useState(false)
  const [error, setError] = useState('')
  const [fatalError, setFatalError] = useState(false)

  useEffect(() => {
    setLoading(true)
    fetchArticle(pageId)
      .then(data => {
        setNewName(data.pageId)
      })
      .catch(e => {
        setFatalError(true)
        setError(e.error || 'Ошибка связи с сервером')
      })
      .finally(() => {
        setLoading(false)
      })
  }, [])

  const onSubmit = useConstCallback(async e => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }

    setSaving(true)
    setError(undefined)
    setSavingSuccess(false)

    const input = {
      pageId: newName,
    }

    try {
      await updateArticle(pageId, input)
      setSavingSuccess(true)
      await sleep(1000)
      setSavingSuccess(false)
      window.scrollTo(window.scrollX, 0)
      window.location.href = `/${newName}`
    } catch (e) {
      setFatalError(false)
      setError(e.error || 'Ошибка связи с сервером')
    } finally {
      setSaving(false)
    }
  })

  const onCancel = useConstCallback(e => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    if (onClose) onClose()
  })

  const onChange = useConstCallback(e => {
    switch (e.target.name) {
      case 'newName':
        setNewName(e.target.value)
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
      <a className="action-area-close btn btn-danger" href="#" onClick={onCancel}>
        Закрыть
      </a>
      <h1>Переименовать/переместить страницу</h1>
      <p>
        Действие <em>переименования</em> изменит "unix-имя" страницы, то есть адрес, по которому доступна страница.{' '}
      </p>

      <form method="POST" onSubmit={onSubmit}>
        <table className="form">
          <tbody>
            <tr>
              <td>Название страницы:</td>
              <td>{pageId}</td>
            </tr>
            <tr>
              <td>Новое название страницы:</td>
              <td>
                <input
                  type="text"
                  name="newName"
                  className={`text ${loading ? 'loading' : ''}`}
                  onChange={onChange}
                  id="page-rename-input"
                  defaultValue={newName}
                  disabled={loading || saving}
                  autoFocus
                />
              </td>
            </tr>
          </tbody>
        </table>
        <div className="buttons form-actions">
          <input type="button" className="btn btn-danger" value="Закрыть" onClick={onCancel} />
          <input type="button" className="btn btn-primary" value="Переименовать/переместить" onClick={onSubmit} />
        </div>
      </form>
    </Styles>
  )
}

export default ArticleRename
