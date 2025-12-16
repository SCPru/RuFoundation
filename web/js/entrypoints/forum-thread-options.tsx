import * as React from 'react'
import { useState } from 'react'
import { updateForumThread } from '../api/forum'
import useConstCallback from '../util/const-callback'
import WikidotModal from '../util/wikidot-modal'

interface CategoryInfo {
  name: string
  id: number
  canMove: boolean
}

interface Props {
  threadId: number
  threadName: string
  threadDescription: string
  canEdit: boolean
  canPin: boolean
  canMove: boolean
  canLock: boolean
  isLocked: boolean
  isPinned: boolean
  categoryId: number
  moveTo: Array<CategoryInfo>
}

interface State {
  isLoading: boolean
  error?: string
  isEditing: boolean
  isMoving: boolean
  editName?: string
  editDescription?: string
  moveCategoryId?: number
}

const ForumThreadOptions: React.FC<Props> = ({
  threadId,
  threadName,
  threadDescription,
  canEdit,
  canPin,
  canMove,
  canLock,
  isLocked,
  isPinned,
  categoryId,
  moveTo,
}: Props) => {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>()
  const [isEditing, setIsEditing] = useState(false)
  const [isMoving, setIsMoving] = useState(false)
  const [editName, setEditName] = useState<string>()
  const [editDescription, setEditDescription] = useState<string>()
  const [moveCategoryId, setMoveCategoryId] = useState<number>()

  const onEdit = useConstCallback(async e => {
    e.preventDefault()
    e.stopPropagation()

    setIsEditing(true)
    setEditName(threadName)
    setEditDescription(threadDescription)
  })

  const onPin = useConstCallback(async e => {
    e.preventDefault()
    e.stopPropagation()

    setIsLoading(true)
    setError(undefined)

    try {
      await updateForumThread({
        threadId,
        isPinned: !isPinned,
      })
    } catch (e) {
      setError(e.error || 'Ошибка связи с сервером')
      setIsLoading(false)
      return
    }

    setIsLoading(false)
    window.location.reload()
  })

  const onLock = useConstCallback(async e => {
    e.preventDefault()
    e.stopPropagation()

    setIsLoading(true)
    setError(undefined)

    try {
      await updateForumThread({
        threadId,
        isLocked: !isLocked,
      })
    } catch (e) {
      setError(e.error || 'Ошибка связи с сервером')
      setIsLoading(false)
      return
    }

    setIsLoading(false)
    window.location.reload()
  })

  const onMove = useConstCallback(async e => {
    e.preventDefault()
    e.stopPropagation()

    setIsMoving(true)
    setMoveCategoryId(categoryId)
  })

  const onCloseError = useConstCallback(() => {
    setError(undefined)
  })

  const onEditCancel = useConstCallback(() => {
    setIsLoading(false)
    setIsEditing(false)
  })

  const onEditSave = useConstCallback(async () => {
    setIsLoading(true)

    try {
      await updateForumThread({
        threadId,
        name: editName,
        description: editDescription,
      })
    } catch (e) {
      setError(e.error || 'Ошибка связи с сервером')
      setIsLoading(false)
      return
    }

    setIsLoading(false)
    window.location.reload()
  })

  const onChange = useConstCallback((k: keyof State, v) => {
    switch (k) {
      case 'editName':
        setEditName(v)
        break
      case 'editDescription':
        setEditDescription(v)
        break
      case 'moveCategoryId':
        setMoveCategoryId(v)
        break
    }
  })

  const renderEdit = useConstCallback(() => {
    return (
      <WikidotModal
        buttons={[
          { title: 'Отмена', onClick: onEditCancel },
          { title: 'Сохранить', onClick: onEditSave },
        ]}
      >
        <h2>Редактировать название и описание темы</h2>
        <hr className="buttons-hr" />
        <table className="form">
          <tbody>
            <tr>
              <td>Заголовок темы:</td>
              <td>
                <input
                  className="text form-control"
                  type="text"
                  value={editName}
                  size={50}
                  maxLength={99}
                  onChange={e => onChange('editName', e.target.value)}
                />
              </td>
            </tr>
            <tr>
              <td>Описание:</td>
              <td>
                <textarea
                  cols={50}
                  rows={2}
                  className="form-control"
                  value={editDescription}
                  onChange={e => onChange('editDescription', e.target.value)}
                />
              </td>
            </tr>
          </tbody>
        </table>
      </WikidotModal>
    )
  })

  const onMoveSave = useConstCallback(async () => {
    setIsLoading(true)

    try {
      await updateForumThread({
        threadId,
        categoryId: moveCategoryId,
      })
    } catch (e) {
      setError(e.error || 'Ошибка связи с сервером')
      setIsLoading(false)
      return
    }

    setIsLoading(false)
    window.location.reload()
  })

  const onMoveCancel = useConstCallback(() => {
    setIsMoving(false)
  })

  const renderMove = useConstCallback(() => {
    return (
      <WikidotModal
        buttons={[
          { title: 'Отмена', onClick: onMoveCancel },
          { title: 'Сохранить', onClick: onMoveSave },
        ]}
      >
        <h2>Переместить тему</h2>
        <hr className="buttons-hr" />
        <table className="form">
          <tbody>
            <tr>
              <td>Укажите новый раздел:</td>
              <td>
                <select className="form-control" value={moveCategoryId} onChange={e => onChange('moveCategoryId', Number.parseInt(e.target.value))}>
                  {moveTo.map(c => (
                    <option key={c.id} disabled={!c.canMove || c.id === categoryId} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </td>
            </tr>
          </tbody>
        </table>
      </WikidotModal>
    )
  })

  if (!canEdit && !canMove && !canLock && !canPin) {
    return null
  }

  return (
    <>
      {isEditing && renderEdit()}
      {isMoving && renderMove()}
      {isLoading && (
        <WikidotModal isLoading>
          <p>Сохранение...</p>
        </WikidotModal>
      )}
      {error && (
        <WikidotModal buttons={[{ title: 'Закрыть', onClick: onCloseError }]} isError>
          <p>
            <strong>Ошибка:</strong> {error}
          </p>
        </WikidotModal>
      )}
      {canEdit && (
        <a href="#" onClick={onEdit} className="btn btn-default btn-small btn-sm">
          Редактировать название и описание
        </a>
      )}{' '}
      {canPin && (
        <a href="#" onClick={onPin} className="btn btn-default btn-small btn-sm">
          {isPinned ? 'Открепить' : 'Закрепить'}
        </a>
      )}{' '}
      {canLock && (
        <a href="#" onClick={onLock} className="btn btn-default btn-small btn-sm">
          {isLocked ? 'Разблокировать' : 'Заблокировать'}
        </a>
      )}{' '}
      {canMove && (
        <a href="#" onClick={onMove} className="btn btn-default btn-small btn-sm">
          Переместить
        </a>
      )}
    </>
  )
}

export default ForumThreadOptions
