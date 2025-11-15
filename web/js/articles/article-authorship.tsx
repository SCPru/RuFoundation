import * as React from 'react'
import { useEffect, useState } from 'react'
import styled from 'styled-components'
import { fetchArticle, updateArticle } from '../api/articles'
import { fetchAllUsers, UserData } from '../api/user'
import AuthorshipEditorComponent from '../components/authorship-editor'
import sleep from '../util/async-sleep'
import useConstCallback from '../util/const-callback'
import Loader from '../util/loader'
import WikidotModal from '../util/wikidot-modal'

interface Props {
  user: UserData
  pageId: string
  isNew?: boolean
  editable?: boolean
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

  .w-authorship-editor-container {
    position: relative;
  }

  /* fixes BHL; without table this looks bad */
  table.form {
    display: table !important;
  }

  .form tr {
    display: table-row !important;
  }

  .form td,
  th {
    display: table-cell !important;
  }
`

const ArticleAuthorship: React.FC<Props> = ({ user, pageId, editable, onClose }) => {
  const [originAuthors, setOriginAuthors] = useState<UserData[]>([])
  const [authors, setAuthors] = useState<UserData[]>([])
  const [allUsers, setAllUsers] = useState<UserData[]>([])
  const [askTransferOwnership, setAskTransferOwnership] = useState(false)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [savingSuccess, setSavingSuccess] = useState(false)
  const [error, setError] = useState('')
  const [fatalError, setFatalError] = useState(false)

  useEffect(() => {
    setLoading(true)
    Promise.all([fetchArticle(pageId), fetchAllUsers()])
      .then(([data, allUsers]) => {
        setOriginAuthors(data.authors)
        setAuthors(data.authors)
        setAllUsers(allUsers)
      })
      .catch(e => {
        setFatalError(true)
        setError(e.error || 'Ошибка связи с сервером')
      })
      .finally(() => {
        setLoading(false)
      })
  }, [])

  const onAskSubmit = useConstCallback(async () => {
    if (authors.length == 0) {
      setError('Должен быть указан хотя бы один автор')
      return
    }
    if (user && originAuthors.includes(user) && !authors.includes(user)) {
      setAskTransferOwnership(true)
    } else {
      await onSubmit()
    }
  })

  const onSubmit = useConstCallback(async () => {
    setSaving(true)
    setError(undefined)
    setSavingSuccess(false)

    const input = {
      pageId: pageId,
      authorsIds: authors.map(x => x.id),
    }

    try {
      await updateArticle(pageId, input)
      setSavingSuccess(true)
      setSaving(false)
      await sleep(1000)
      setSavingSuccess(false)
      window.scrollTo(window.scrollX, 0)
      window.location.reload()
    } catch (e) {
      setFatalError(false)
      setError(e.error || 'Ошибка связи с сервером')
    } finally {
      setSaving(false)
    }
  })

  const onCancelTransferOwnership = useConstCallback(() => {
    setAskTransferOwnership(false)
  })

  const onClear = useConstCallback(e => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    setAuthors([])
  })

  const onCancel = useConstCallback(e => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    if (onClose) onClose()
  })

  const onCloseError = useConstCallback(() => {
    setError(null)
    if (fatalError) {
      onCancel(null)
    }
  })

  const onChange = useConstCallback((authors: UserData[]) => {
    setAuthors(authors)
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
      {askTransferOwnership && (
        <WikidotModal
          buttons={[
            { title: 'Отмена', onClick: onCancelTransferOwnership },
            { title: 'Да, отказаться', onClick: onSubmit },
          ]}
        >
          <h1>Отказаться от авторства страницы?</h1>
          <p>
            Обратите внимание, что вернуть вам авторство страницы сможет только человек, указаный в качестве автора этой страницы или администрация
            сайта
          </p>
        </WikidotModal>
      )}
      <a className="action-area-close btn btn-danger" href="#" onClick={onCancel}>
        Закрыть
      </a>
      <h1>Авторство страницы</h1>

      <form method="POST" onSubmit={onSubmit}>
        <table className="form">
          <tbody>
            <tr>
              <td>Авторы:</td>
            </tr>
            <tr>
              <td className="w-authorship-editor-container">
                {loading && <Loader className="loader" />}
                <AuthorshipEditorComponent authors={authors} allUsers={allUsers} onChange={onChange} editable={editable} />
              </td>
            </tr>
          </tbody>
        </table>
        {editable && (
          <div className="buttons form-actions">
            <input type="button" className="btn btn-danger" value="Закрыть" onClick={onCancel} />
            <input type="button" className="btn btn-default" value="Очистить" onClick={onClear} />
            <input type="button" className="btn btn-primary" value="Сохранить" onClick={onAskSubmit} />
          </div>
        )}
      </form>
    </Styles>
  )
}

export default ArticleAuthorship
