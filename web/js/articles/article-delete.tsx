import * as React from 'react'
import { useEffect, useState } from 'react'
import styled from 'styled-components'
import { ArticleUpdateRequest, deleteArticle, fetchArticle, updateArticle } from '../api/articles'
import sleep from '../util/async-sleep'
import useConstCallback from '../util/const-callback'
import WikidotModal from '../util/wikidot-modal'

interface Props {
  pageId: string
  onClose?: () => void
  canDelete?: boolean
  canRename?: boolean
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

const ArticleDelete: React.FC<Props> = ({ pageId, onClose, canDelete, canRename }) => {
  const [permanent, setPermanent] = useState(false)
  const [newName, setNewName] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [savingSuccess, setSavingSuccess] = useState(false)
  const [error, setError] = useState('')
  const [fatalError, setFatalError] = useState(false)

  useEffect(() => {
    setLoading(true)
    fetchArticle(pageId)
      .then(data => {
        setNewName('deleted:' + data.pageId)
        setPermanent(Boolean(canDelete && !canRename))
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
    setError('')
    setSavingSuccess(false)

    try {
      let actualNewName = newName
      if (!permanent) {
        const input: ArticleUpdateRequest = {
          pageId: newName,
          tags: [],
          forcePageId: true,
        }
        const result = await updateArticle(pageId, input)
        actualNewName = result.pageId
      } else {
        await deleteArticle(pageId)
      }
      setSaving(false)
      setSavingSuccess(true)
      await sleep(1000)
      setSavingSuccess(false)
      window.scrollTo(window.scrollX, 0)
      if (!permanent) {
        window.location.href = `/${actualNewName}`
      } else {
        window.location.reload()
      }
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
      case 'permanent':
        if (canRename) setPermanent(!permanent)
        break
    }
  })

  const onCloseError = useConstCallback(() => {
    setError('')
    if (fatalError) {
      onCancel(null)
    }
  })

  const isAlreadyDeleted = pageId.toLowerCase().startsWith('deleted:')

  if (isAlreadyDeleted && !canDelete) {
    return (
      <Styles>
        <a className="action-area-close btn btn-danger" href="#" onClick={onCancel}>
          Закрыть
        </a>
        <h1>Удалить страницу</h1>
        <p>Эта страница уже считается удалённой, поскольку находится в категории "deleted". Вы не можете удалить её ещё сильнее.</p>
      </Styles>
    )
  }

  return (
    <Styles>
      {saving && (
        <WikidotModal isLoading>
          <p>Удаление...</p>
        </WikidotModal>
      )}
      {savingSuccess && (
        <WikidotModal>
          <p>Успешно удалено!</p>
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
      <h1>Удалить страницу</h1>
      {canDelete ? (
        <p>Вы можете удалить страницу, либо переместив её в категорию "deleted", либо удалить её навсегда (это безвозвратно, будьте осторожны).</p>
      ) : (
        <p>Вы можете удалить страницу, переместив её в категорию "deleted". Полное удаление недоступно.</p>
      )}

      {canDelete && (
        <table className="form">
          <tbody>
            <tr>
              <td>Что делать?</td>
              <td>
                <input
                  type="checkbox"
                  name="permanent"
                  className={`text ${loading ? 'loading' : ''}`}
                  onChange={onChange}
                  id="page-rename-input"
                  checked={!permanent}
                  disabled={loading || saving || !canRename}
                />
                <label htmlFor="page-rename-input">Переименовать{!canRename && ' (недоступно)'}</label>
              </td>
            </tr>
            <tr>
              <td></td>
              <td>
                <input
                  type="checkbox"
                  name="permanent"
                  className={`text ${loading ? 'loading' : ''}`}
                  onChange={onChange}
                  id="page-permanent-input"
                  checked={permanent}
                  disabled={loading || saving}
                />
                <label htmlFor="page-permanent-input">Удалить навсегда</label>
              </td>
            </tr>
          </tbody>
        </table>
      )}

      {!permanent ? (
        <form method="POST" onSubmit={onSubmit}>
          <p>
            Установив странице префикс "deleted:" вы переместите её в другую категорию (пространство имён). Это более-менее эквивалентно удалению, но
            информация не будет потеряна.
          </p>
          {isAlreadyDeleted && (
            <p>
              <strong>Внимание:</strong> Статья уже находится в категории "deleted". Если вы хотите удалить её ещё сильнее, воспользуйтесь опцией
              "Удалить навсегда".
            </p>
          )}
          <div className="buttons form-actions">
            <input type="button" className="btn btn-danger" value="Отмена" onClick={onCancel} />
            {!isAlreadyDeleted && <input type="button" className="btn btn-primary" value={'Переместить в категорию "deleted"'} onClick={onSubmit} />}
          </div>
        </form>
      ) : (
        <form method="POST" onSubmit={onSubmit}>
          <p>Это приведет к полному удалению страницы и невозможности восстановления данных. Вы уверены, что хотите это сделать?</p>
          <div className="buttons form-actions">
            <input type="button" className="btn btn-danger" value="Отмена" onClick={onCancel} />
            <input type="button" className="btn btn-primary" value="Удалить" onClick={onSubmit} />
          </div>
        </form>
      )}
    </Styles>
  )
}

export default ArticleDelete
