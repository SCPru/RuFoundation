import { Editor } from '@monaco-editor/react'
import { editor } from 'monaco-editor'
import * as React from 'react'
import { useEffect, useRef, useState } from 'react'
import styled from 'styled-components'
import { fetchForumPost, previewForumPost } from '../api/forum'
import { fetchAllUsers } from '../api/user'
import useConstCallback from '../util/const-callback'
import Loader from '../util/loader'
import WikidotModal from '../util/wikidot-modal'

export interface ForumPostPreviewData {
  name: string
  description: string
  content: string
}

export interface ForumPostSubmissionData {
  name: string
  description: string
  source: string
}

interface Props {
  initialTitle?: string
  isThread?: boolean
  onSubmit?: (input: ForumPostSubmissionData) => Promise<void>
  onPreview?: (result: ForumPostPreviewData) => void
  onClose?: () => void
  isNew?: boolean
  postId?: number
}

const Styles = styled.div`
  .w-editor-area {
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

const StyledEditor = styled(Editor)`
  border: 1px solid #ccc;

  div {
    max-width: none !important;
  }
`

const ForumPostEditor: React.FC<Props> = ({
  initialTitle,
  isThread,
  onSubmit: onSubmitDelegate,
  onPreview: onPreviewDelegate,
  onClose: onCloseDelegate,
  isNew,
  postId,
}) => {
  const [name, setName] = useState(initialTitle || '')
  const [description, setDescription] = useState('')
  const [source, setSource] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [savingSuccess, setSavingSuccess] = useState(false)
  const [error, setError] = useState('')
  const [fatalError, setFatalError] = useState(false)
  const [usernameSet, setUsernameSet] = useState<Set<string>>(new Set())
  const [mentionDecorationIds, setMentionDecorationIds] = useState<string[]>([])

  const editorRef = useRef(null)
  const monacoRef = useRef(null)

  const monacoOptions: editor.IStandaloneEditorConstructionOptions = {
    minimap: { enabled: false },
    wordWrap: 'on',
    lineNumbers: 'off',
    lineDecorationsWidth: 0,
    lineNumbersMinChars: 0,
    glyphMargin: false,
    folding: false,
    quickSuggestions: false,
    readOnly: loading || saving,
  }

  const handleRefresh = useConstCallback(e => {
    if (!saving) {
      e.preventDefault()
      e.returnValue = ''
    }
  })

  useEffect(() => {
    window.addEventListener('beforeunload', handleRefresh)
    ;(window as any)._closePostEditor = () => {
      onCancel(undefined)
    }
    if (!isNew) {
      setLoading(true)
      fetchForumPost(postId)
        .then(data => {
          setSource(data.source)
          setName(data.name)
        })
        .catch(e => {
          setFatalError(true)
          setError(e.error || 'Ошибка связи с сервером')
        })
        .finally(() => {
          setLoading(false)
        })
    }

    fetchAllUsers()
      .then(users => {
        setUsernameSet(new Set(users.filter(u => u.type === 'normal' || u.type === 'bot').map(u => u.username.toLowerCase())))
      })
      .catch(e => {
        setFatalError(false)
        setError(e.error || 'Ошибка связи с сервером')
      })

    return () => {
      window.removeEventListener('beforeunload', handleRefresh)
      ;(window as any)._closePostEditor = undefined
    }
  }, [])

  useEffect(() => {
    highlightMentions(source)
  }, [source, usernameSet])

  const onEditorDidMount = useConstCallback((editor, monaco) => {
    editorRef.current = editor
    monacoRef.current = monaco
  })

  const highlightMentions = useConstCallback((text: string) => {
    const editor = editorRef.current
    const monaco = monacoRef.current
    if (!editor || !monaco) return

    const model = editorRef.current.getModel()
    if (!model) return

    const mentionRegex = /@[\w.-]+/g
    const newDecorations: editor.IModelDeltaDecoration[] = []
    let match

    while ((match = mentionRegex.exec(source)) !== null) {
      const mention = match[0]
      const username = mention.substring(1)

      if (usernameSet.has(username)) {
        const startPos = model.getPositionAt(match.index)
        const endPos = model.getPositionAt(match.index + mention.length)
        const range = new monaco.Range(startPos.lineNumber, startPos.column, endPos.lineNumber, endPos.column)

        newDecorations.push({
          range: range,
          options: {
            inlineClassName: 'w-user-mention',
          },
        })
      }
    }

    const newMentionIds = editor.deltaDecorations(mentionDecorationIds, newDecorations)
    setMentionDecorationIds(newMentionIds)
  })

  const highlightMentionsStr = useConstCallback((text: string) => {
    const regex = /@[\w.-]+/g

    return text.replace(regex, full => {
      const username = full.slice(1)
      if (usernameSet.has(username.toLowerCase())) {
        return `<span class="w-user-mention">${full}</span>`
      }
      return full
    })
  })

  const onSubmit = useConstCallback(async e => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    if (onSubmitDelegate) {
      const input: ForumPostSubmissionData = {
        name: name,
        description,
        source,
      }
      setSaving(true)
      setError(null)
      setSavingSuccess(false)
      try {
        await onSubmitDelegate(input)
        setError(null)
        setSavingSuccess(false)
        setSource('')
        setName(initialTitle)
      } catch (e) {
        setLoading(false)
        setFatalError(false)
        setError(e.message || e.error || 'Ошибка связи с сервером')
      } finally {
        setSaving(false)
      }
    }
  })

  const onPreview = useConstCallback(async e => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    if (onPreviewDelegate) {
      const { result: rendered } = await previewForumPost(source)
      const input: ForumPostPreviewData = {
        name: name,
        description,
        content: highlightMentionsStr(rendered),
      }
      onPreviewDelegate(input)
    }
  })

  const onCancel = useConstCallback(e => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    if (onCloseDelegate) {
      onCloseDelegate()
    }
  })

  const onInputChange = useConstCallback(e => {
    const { name, value } = e.target
    if (name === 'name') {
      setName(value)
    } else if (name === 'description') {
      setDescription(value)
    }
  })

  const onSourceChange = useConstCallback((value: string) => {
    setSource(value || '')
  })

  const onCloseError = useConstCallback(() => {
    setError(null)
    if (fatalError) {
      onCancel(null)
    }
  })

  // todo: check if this ID is actually used anywhere. if not, we can drop it
  let formId = 'edit-post-form'
  if (isNew && isThread) {
    formId = 'new-thread-form'
  } else if (isNew) {
    formId = 'new-post-form'
  }

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
      <form id={formId} onSubmit={onSubmit}>
        <table className="form" style={{ margin: '1em 0' }}>
          <tbody>
            <tr>
              <td>Заголовок {isThread ? 'темы' : 'сообщения'}:</td>
              <td>
                <input
                  className="text form-control"
                  value={name}
                  onChange={onInputChange}
                  name="name"
                  type="text"
                  size={35}
                  maxLength={128}
                  style={{ fontWeight: 'bold', fontSize: '130%' }}
                  disabled={loading || saving}
                />
              </td>
            </tr>
            {isThread && (
              <tr>
                <td>Короткое описание темы:</td>
                <td>
                  <textarea
                    cols={40}
                    rows={2}
                    className="form-control"
                    value={description}
                    onChange={onInputChange}
                    name="description"
                    maxLength={1000}
                    disabled={loading || saving}
                  />
                </td>
              </tr>
            )}
          </tbody>
        </table>
        {/* This is not supported right now but we have to add empty div for BHL */}
        <div id="wd-editor-toolbar-panel" className="wd-editor-toolbar-panel" />
        <div className={`w-editor-area ${loading ? 'loading' : ''}`}>
          <StyledEditor
            className="form-control"
            loading="Загрузка, терпите, карлики..."
            height="250px"
            value={source}
            onChange={onSourceChange}
            onMount={onEditorDidMount}
            options={monacoOptions}
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
            value="Отправить"
            onClick={onSubmit}
            disabled={loading || saving}
          />
        </div>
      </form>
    </Styles>
  )
}

export default ForumPostEditor
