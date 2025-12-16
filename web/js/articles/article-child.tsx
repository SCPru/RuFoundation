import * as React from 'react'
import { useRef, useState } from 'react'
import styled from 'styled-components'
import useConstCallback from '../util/const-callback'
import { isFullNameAllowed } from '../util/validate-article-name'
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

const ArticleChild: React.FC<Props> = ({ pageId, onClose }) => {
  const [child, setChild] = useState('')
  const [error, setError] = useState('')
  const inputRef = useRef<HTMLInputElement | null>(null)

  const onSubmit = useConstCallback(async e => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }

    if (isFullNameAllowed(child) && child != pageId) {
      window.location.href = `/${child}/edit/true/parent/${pageId}`
    } else {
      setError('Некорректный ID дочерней страницы!')
    }
  })

  const onCancel = useConstCallback(e => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    if (onClose) onClose()
  })

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    switch (e.target.name) {
      case 'child':
        setChild(e.target.value)
        break
    }
  }

  const onCloseError = () => {
    setError('')
  }

  const onSnippet = useConstCallback((e: React.MouseEvent, value: string) => {
    e.preventDefault()
    e.stopPropagation()
    inputRef.current?.focus()
    setChild(value)
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
      <a className="action-area-close btn btn-danger" href="#" onClick={onCancel}>
        Закрыть
      </a>
      <h1>Создать дочернюю страницу</h1>
      <p>Это действие создаст страницу, в качестве родителя которой будет установлена данная страница.</p>
      <p>
        {' '}
        <em>Подсказки:</em> <a onClick={e => onSnippet(e, 'fragment:')}>fragment:</a> /{' '}
        <a onClick={e => onSnippet(e, `fragment:${pageId}_`)}>{`fragment:${pageId}_`}</a>
      </p>

      <form method="POST" onSubmit={onSubmit}>
        <table className="form">
          <tbody>
            <tr>
              <td>Название этой страницы:</td>
              <td>{pageId}</td>
            </tr>
            <tr>
              <td>Название дочерней страницы:</td>
              <td>
                <input ref={inputRef} type="text" name="child" className="text" onChange={onChange} id="page-child-input" value={child} autoFocus />
              </td>
            </tr>
          </tbody>
        </table>
        <div className="buttons form-actions">
          <input type="button" className="btn btn-danger" value="Закрыть" onClick={onCancel} />
          <input type="button" className="btn btn-primary" value="Создать" onClick={onSubmit} />
        </div>
      </form>
    </Styles>
  )
}

export default ArticleChild
