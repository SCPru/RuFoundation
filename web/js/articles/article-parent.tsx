import * as React from 'react'
import { useEffect, useState } from 'react'
import styled from 'styled-components'
import { fetchArticle, updateArticle } from '../api/articles'
import sleep from '../util/async-sleep'
import useConstCallback from '../util/const-callback'
import WikidotModal from '../util/wikidot-modal'

interface Props {
  pageId: string
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

const ArticleParent: React.FC<Props> = ({ pageId, onClose }) => {
  const [parent, setParent] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [savingSuccess, setSavingSuccess] = useState(false)
  const [error, setError] = useState('')
  const [fatalError, setFatalError] = useState(false)

  useEffect(() => {
    setLoading(true)
    fetchArticle(pageId)
      .then(data => {
        setParent(data.parent)
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
      pageId: pageId,
      parent: parent,
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

  const onCancel = useConstCallback(e => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    if (onClose) onClose()
  })

  const onChange = useConstCallback(e => {
    switch (e.target.name) {
      case 'parent':
        setParent(e.target.value)
        break
    }
  })

  const onClear = useConstCallback(e => {
    setParent('')
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
      <h1>Родительская страница и цепочка навигации</h1>
      <p>
        Хотите создать крутую цепочку навигации "назад"? Структуировать сайт? Установите родительскую страницу (один уровень выше) для этой страницы.
      </p>
      <p>
        Если Вы не хотите{' '}
        <a
          href="https://ru.wikipedia.org/wiki/%D0%9D%D0%B0%D0%B2%D0%B8%D0%B3%D0%B0%D1%86%D0%B8%D0%BE%D0%BD%D0%BD%D0%B0%D1%8F_%D1%86%D0%B5%D0%BF%D0%BE%D1%87%D0%BA%D0%B0"
          target="_blank"
        >
          навигационную цепочку
        </a>{' '}
        для этой страницы - просто оставьте поле ввода - пустым.
      </p>

      <form method="POST" onSubmit={onSubmit}>
        <table className="form">
          <tbody>
            <tr>
              <td>Название родительской страницы:</td>
              <td>
                <input
                  type="text"
                  name="parent"
                  className={`text ${loading ? 'loading' : ''}`}
                  onChange={onChange}
                  id="page-parent-input"
                  defaultValue={parent}
                  disabled={loading || saving}
                />
              </td>
            </tr>
          </tbody>
        </table>
        <div className="buttons form-actions">
          <input type="button" className="btn btn-danger" value="Закрыть" onClick={onCancel} />
          <input type="button" className="btn btn-default" value="Очистить" onClick={onClear} />
          <input type="button" className="btn btn-primary" value="Установить родителя" onClick={onSubmit} />
        </div>
      </form>
    </Styles>
  )
}

export default ArticleParent
