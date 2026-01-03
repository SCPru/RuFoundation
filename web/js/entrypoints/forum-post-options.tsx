import React, { useEffect, useRef, useState } from 'react'
import { renderTo, unmountFromRoot } from '~util/react-render-into'
import {
  createForumPost,
  deleteForumPost,
  fetchForumPost,
  fetchForumPostVersions,
  ForumNewPostRequest,
  ForumPostVersion,
  ForumUpdatePostRequest,
  updateForumPost,
} from '../api/forum'
import { UserData } from '../api/user'
import ForumPostEditor, { ForumPostPreviewData, ForumPostSubmissionData } from '../forum/forum-post-editor'
import ForumPostPreview from '../forum/forum-post-preview'
import useConstCallback from '../util/const-callback'
import formatDate from '../util/date-format'
import UserView from '../util/user-view'
import WikidotModal from '../util/wikidot-modal'

interface Props {
  user: UserData
  threadId: number
  threadName: string
  postId: number
  postName: string
  canReply?: boolean
  canEdit?: boolean
  canDelete?: boolean
  canReact?: boolean
  hasRevisions?: boolean
  lastRevisionDate?: string
  lastRevisionAuthor?: UserData
  preferences?: { [key: string]: any }
}

const ForumPostOptions: React.FC<Props> = ({
  user,
  threadId,
  threadName,
  postId,
  postName,
  canReply,
  canEdit,
  canDelete,
  canReact,
  hasRevisions,
  lastRevisionDate,
  lastRevisionAuthor,
  preferences,
}) => {
  const [isEditing, setIsEditing] = useState(false)
  const [isReplying, setIsReplying] = useState(false)
  const [open, setOpen] = useState(false)
  const [originalPreviewTitle, setOriginalPreviewTitle] = useState('')
  const [originalPreviewContent, setOriginalPreviewContent] = useState('')
  const [deleteError, setDeleteError] = useState('')
  const [revisionsOpen, setRevisionsOpen] = useState(false)
  const [currentRevision, setCurrentRevision] = useState('')
  const [revisions, setRevisions] = useState<Array<ForumPostVersion>>([])

  const refSelf = useRef<HTMLElement>()
  const refPreviewTitle = useRef<HTMLElement>()
  const refPreviewContent = useRef<HTMLElement>()
  const refReplyPreview = useRef<HTMLElement>()

  useEffect(() => {
    if (!refSelf.current) {
      // something bad happened
      return
    }
    const longPost = refSelf.current.parentNode
    if (!longPost) {
      return
    }
    refPreviewTitle.current = (longPost.querySelector('.head .title') as HTMLElement | null) ?? undefined
    refPreviewContent.current = (longPost.querySelector('.content') as HTMLElement | null) ?? undefined
    let newRefReplyPreview: HTMLElement | undefined = (longPost.querySelector('.w-reply-preview') as HTMLElement | null) ?? undefined
    if (!newRefReplyPreview) {
      newRefReplyPreview = document.createElement('div')
      newRefReplyPreview.className = 'w-reply-preview'
      if (refSelf.current.parentNode) {
        refSelf.current.parentNode.insertBefore(newRefReplyPreview, refSelf.current)
      }
    }
    refReplyPreview.current = newRefReplyPreview
    setOriginalPreviewTitle(refPreviewTitle.current?.textContent ?? '')
    setOriginalPreviewContent(refPreviewContent.current?.innerHTML ?? '')
  }, [])

  const onReplyClose = useConstCallback(() => {
    setIsReplying(false)
    if (refReplyPreview.current?.firstChild) {
      unmountFromRoot(refReplyPreview.current)
      refReplyPreview.current.innerHTML = ''
    }
  })

  const onReplySubmit = useConstCallback(async (input: ForumPostSubmissionData) => {
    const request: ForumNewPostRequest = {
      threadId,
      replyTo: postId,
      name: input.name,
      source: input.source,
    }

    const { url } = await createForumPost(request)
    onReplyClose()

    window.onhashchange = () => {
      window.location.reload()
    }

    window.location.href = url
  })

  const onReplyPreview = useConstCallback((input: ForumPostPreviewData) => {
    if (!refReplyPreview.current) {
      return
    }
    renderTo(refReplyPreview.current, <ForumPostPreview preview={input} user={user} />)
  })

  const onReply = useConstCallback(e => {
    e.preventDefault()
    e.stopPropagation()
    const closeCurrent = (window as any)._closePostEditor
    if (closeCurrent) {
      closeCurrent()
    }
    setIsReplying(true)
  })

  const onEditClose = useConstCallback(() => {
    if (refPreviewTitle.current) {
      refPreviewTitle.current.textContent = originalPreviewTitle
    }
    if (refPreviewContent.current) {
      refPreviewContent.current.innerHTML = originalPreviewContent
    }
    setIsEditing(false)
  })

  const onEditSubmit = useConstCallback(async (input: ForumPostSubmissionData) => {
    const request: ForumUpdatePostRequest = {
      postId,
      name: input.name,
      source: input.source,
    }
    const result = await updateForumPost(request)
    if (refPreviewTitle.current) {
      refPreviewTitle.current.textContent = result.name
    }
    if (refPreviewContent.current) {
      refPreviewContent.current.innerHTML = result.content
    }
    setOriginalPreviewTitle(result.name)
    setOriginalPreviewContent(result.content)
    onEditClose()
  })

  const onEditPreview = useConstCallback((input: ForumPostPreviewData) => {
    if (refPreviewTitle.current) {
      refPreviewTitle.current.textContent = input.name
    }
    if (refPreviewContent.current) {
      refPreviewContent.current.innerHTML = input.content
    }
    setRevisionsOpen(false)
    setCurrentRevision('')
  })

  const onEdit = useConstCallback(e => {
    e.preventDefault()
    e.stopPropagation()
    const closeCurrent = (window as any)._closePostEditor
    if (closeCurrent) {
      closeCurrent()
    }
    setIsEditing(true)
  })

  const onDelete = useConstCallback(e => {
    e.preventDefault()
    e.stopPropagation()

    deleteForumPost(postId)
      .then(() => {
        // successful deletion. reflect the changes (drop the current post / tree)
        // first, unmount self. this makes sure any editors are taken care of
        const post = refSelf.current?.parentElement?.parentElement // should point to class .post
        if (refSelf.current) {
          unmountFromRoot(refSelf.current)
        }
        const parent = post?.parentElement
        if (parent) {
          parent.removeChild(post)
          if (parent.classList.contains('post-container') && parent.parentElement?.classList.contains('post-container')) {
            // check if parent element has no children anymore
            if (!parent.firstElementChild) {
              parent.parentNode?.removeChild(parent)
            }
          }
        }
      })
      .catch(e => {
        setDeleteError(e.error || 'Ошибка связи с сервером')
      })
  })

  const onToggle = useConstCallback(e => {
    e.preventDefault()
    e.stopPropagation()

    setOpen(!open)
  })

  const onCloseError = useConstCallback(() => {
    setDeleteError('')
  })

  const onOpenRevisions = useConstCallback(e => {
    e.preventDefault()
    e.stopPropagation()

    fetchForumPostVersions(postId)
      .then(revisions => {
        setRevisionsOpen(true)
        setRevisions(revisions.versions)
      })
      .catch(e => {
        setRevisionsOpen(false)
        setDeleteError(e.error || 'Ошибка связи с сервером')
      })
  })

  const onCloseRevisions = useConstCallback(e => {
    e.preventDefault()
    e.stopPropagation()

    if (currentRevision) {
      if (refPreviewTitle.current) {
        refPreviewTitle.current.textContent = originalPreviewTitle
      }
      if (refPreviewContent.current) {
        refPreviewContent.current.innerHTML = originalPreviewContent
      }
    }
    setRevisionsOpen(false)
    setCurrentRevision('')
  })

  const onShowRevision = useConstCallback((e, date) => {
    e.preventDefault()
    e.stopPropagation()

    fetchForumPost(postId, date).then(data => {
      setCurrentRevision(date)
      if (refPreviewTitle.current) {
        refPreviewTitle.current.textContent = data.name
      }
      if (refPreviewContent.current) {
        refPreviewContent.current.innerHTML = data.content
      }
    })
  })

  return (
    <>
      {hasRevisions && lastRevisionDate && lastRevisionAuthor && !revisionsOpen && (
        <div className="changes" style={{ display: 'block' }}>
          Последнее редактирование{' '}
          <span className="odate" style={{ display: 'inline' }}>
            {formatDate(new Date(lastRevisionDate))}
          </span>{' '}
          от <UserView data={lastRevisionAuthor} hideAvatar />{' '}
          <a href="#" onClick={onOpenRevisions}>
            <i className="icon-plus" /> Показать ещё
          </a>
        </div>
      )}
      {revisionsOpen && (
        <div className="revisions" style={{ display: 'block' }}>
          <a href="#" onClick={onCloseRevisions}>
            - Скрыть
          </a>
          <div className="title">Версии сообщения</div>
          <table className="table">
            <tbody>
              {(revisions || []).map((rev, i) => (
                <tr className={currentRevision === rev.createdAt || (i === 0 && !currentRevision) ? 'active' : ''} key={i}>
                  <td>
                    <UserView data={rev.author} hideAvatar />
                  </td>
                  <td>{formatDate(new Date(rev.createdAt))}</td>
                  <td>
                    <a href="#" onClick={e => onShowRevision(e, rev.createdAt)}>
                      Показать правки
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div style={{ display: 'none' }} ref={r => (refSelf.current = r?.parentElement ?? undefined)} />
      {deleteError && (
        <WikidotModal buttons={[{ title: 'Закрыть', onClick: onCloseError }]} isError>
          <p>
            <strong>Ошибка:</strong> {deleteError}
          </p>
        </WikidotModal>
      )}
      {canReply && (
        <strong>
          <a href="#" onClick={onReply}>
            Ответить
          </a>
        </strong>
      )}{' '}
      {(canEdit || canDelete) && (
        <a href="#" onClick={onToggle}>
          Опции
        </a>
      )}
      {open && (
        <div className="options">
          {canEdit && (
            <a href="#" onClick={onEdit}>
              Редактировать
            </a>
          )}{' '}
          {canDelete && (
            <a href="#" onClick={onDelete}>
              Удалить
            </a>
          )}
        </div>
      )}
      {isReplying && (
        <div className="post-container">
          <ForumPostEditor
            isNew
            useAdvancedEditor={preferences?.['qol__advanced_source_editor_enabled'] === true}
            onClose={onReplyClose}
            onSubmit={onReplySubmit}
            onPreview={onReplyPreview}
            initialTitle={'Re: ' + (postName || threadName)}
          />
        </div>
      )}
      {isEditing && (
        <ForumPostEditor
          postId={postId}
          useAdvancedEditor={preferences?.['qol__advanced_source_editor_enabled'] === true}
          onClose={onEditClose}
          onSubmit={onEditSubmit}
          onPreview={onEditPreview}
        />
      )}
    </>
  )
}

export default ForumPostOptions
