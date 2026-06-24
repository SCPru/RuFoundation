import React, { useEffect, useLayoutEffect, useRef, useState } from 'react'
import * as ReactDOM from 'react-dom'
import { renderTo, unmountFromRoot } from '~util/react-render-into'
import {
  addForumPostReaction,
  createForumPost,
  deleteForumPost,
  fetchForumPost,
  fetchForumPostVersions,
  ForumNewPostRequest,
  ForumPostReactionState,
  ForumPostReactionSummary,
  ForumPostVersion,
  ForumReaction,
  ForumReactionLimits,
  ForumUpdatePostRequest,
  removeAllForumPostReactions,
  removeForumPostReaction,
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
  canRemoveOwnReactions?: boolean
  canModerateReactions?: boolean
  canUseInactiveReactions?: boolean
  availableReactions?: Array<ForumReaction>
  reactions?: Array<ForumPostReactionSummary>
  reactionLimits?: ForumReactionLimits
  reactionTotalCount?: number
  myReactionCount?: number
  hasRevisions?: boolean
  lastRevisionDate?: string
  lastRevisionAuthor?: UserData
  preferences?: { [key: string]: any }
}

function navigateToForumPost(url: string) {
  const detail = { url, handled: false }
  window.dispatchEvent(new CustomEvent('forum:post-created', { detail }))
  if (!detail.handled) {
    window.location.href = url
  }
}

function fitFloatingElementToViewport(element?: HTMLElement | null) {
  if (!element) {
    return
  }

  const margin = 8
  const anchor = element.parentElement
  const viewportWidth = document.documentElement.clientWidth
  const viewportHeight = document.documentElement.clientHeight
  const anchorRect = anchor?.getBoundingClientRect()

  element.classList.remove('is-above')
  element.style.removeProperty('--forum-popup-shift-x')
  element.style.removeProperty('max-height')
  element.style.removeProperty('overflow-y')

  let rect = element.getBoundingClientRect()
  const availableBelow = viewportHeight - (anchorRect?.bottom ?? rect.top) - margin
  const availableAbove = (anchorRect?.top ?? rect.top) - margin
  if (rect.bottom > viewportHeight - margin && availableAbove > availableBelow) {
    element.classList.add('is-above')
    rect = element.getBoundingClientRect()
  }

  const availableVerticalSpace = element.classList.contains('is-above') ? availableAbove : availableBelow
  if (rect.height > availableVerticalSpace) {
    element.style.maxHeight = `${Math.max(96, availableVerticalSpace)}px`
    element.style.overflowY = 'auto'
    rect = element.getBoundingClientRect()
  }

  let shiftX = 0
  if (rect.right > viewportWidth - margin) {
    shiftX -= rect.right - (viewportWidth - margin)
  }
  if (rect.left + shiftX < margin) {
    shiftX += margin - (rect.left + shiftX)
  }
  element.style.setProperty('--forum-popup-shift-x', `${Math.round(shiftX)}px`)
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
  canRemoveOwnReactions,
  canModerateReactions,
  canUseInactiveReactions,
  availableReactions = [],
  reactions = [],
  reactionLimits = { maxPerUser: 0, maxPerPost: 0 },
  reactionTotalCount,
  myReactionCount,
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
  const [reactionState, setReactionState] = useState<ForumPostReactionState>(() => ({
    availableReactions,
    reactions,
    limits: reactionLimits,
    totalCount: reactionTotalCount ?? reactions.reduce((sum, item) => sum + item.count, 0),
    myCount: myReactionCount ?? reactions.filter(item => item.me).length,
    canReact: canReact === true,
    canRemoveOwnReactions: canRemoveOwnReactions === true,
    canModerateReactions: canModerateReactions === true,
    canUseInactiveReactions: canUseInactiveReactions === true,
  }))
  const [reactionPickerOpen, setReactionPickerOpen] = useState(false)
  const [reactionListOpen, setReactionListOpen] = useState(false)
  const [activeReactionId, setActiveReactionId] = useState<number | null>(null)
  const [reactionError, setReactionError] = useState('')
  const [reactionLoading, setReactionLoading] = useState(false)
  const [menuPortal, setMenuPortal] = useState<HTMLElement | null>(null)

  const refSelf = useRef<HTMLElement>()
  const refPreviewTitle = useRef<HTMLElement>()
  const refPreviewContent = useRef<HTMLElement>()
  const refReplyPreview = useRef<HTMLElement>()
  const refReactionPicker = useRef<HTMLElement>()
  const refReactionPickerDropdown = useRef<HTMLElement>()
  const refPostMenu = useRef<HTMLElement>()
  const refPostMenuDropdown = useRef<HTMLElement>()

  useLayoutEffect(() => {
    if (!refSelf.current) {
      // something bad happened
      return
    }
    const longPost = refSelf.current.closest('.long') as HTMLElement | null
    if (!longPost) {
      return
    }
    refPreviewTitle.current = (longPost.querySelector('.head .title') as HTMLElement | null) ?? undefined
    refPreviewContent.current = (longPost.querySelector('.content') as HTMLElement | null) ?? undefined
    const head = longPost.querySelector('.head') as HTMLElement | null
    const menuSlot = document.createElement('div')
    menuSlot.className = 'forum-post-menu-slot'
    if (head) {
      head.insertBefore(menuSlot, head.firstChild)
      setMenuPortal(menuSlot)
    }
    let newRefReplyPreview: HTMLElement | undefined = (longPost.querySelector('.w-reply-preview') as HTMLElement | null) ?? undefined
    if (!newRefReplyPreview) {
      newRefReplyPreview = document.createElement('div')
      newRefReplyPreview.className = 'w-reply-preview'
      longPost.insertBefore(newRefReplyPreview, refSelf.current)
    }
    refReplyPreview.current = newRefReplyPreview
    setOriginalPreviewTitle(refPreviewTitle.current?.textContent ?? '')
    setOriginalPreviewContent(refPreviewContent.current?.innerHTML ?? '')

    return () => {
      if (menuSlot.parentElement) {
        menuSlot.parentElement.removeChild(menuSlot)
      }
    }
  }, [])

  useEffect(() => {
    if (!open) {
      return
    }

    const onDocumentMouseDown = (e: MouseEvent | TouchEvent) => {
      const target = e.target
      if (target instanceof Node && refPostMenu.current?.contains(target)) {
        return
      }
      setOpen(false)
    }

    document.addEventListener('mousedown', onDocumentMouseDown)
    document.addEventListener('touchstart', onDocumentMouseDown)

    return () => {
      document.removeEventListener('mousedown', onDocumentMouseDown)
      document.removeEventListener('touchstart', onDocumentMouseDown)
    }
  }, [open])

  useLayoutEffect(() => {
    if (!open) {
      return
    }

    const updatePosition = () => fitFloatingElementToViewport(refPostMenuDropdown.current)
    updatePosition()
    window.addEventListener('resize', updatePosition)
    window.addEventListener('scroll', updatePosition, true)

    return () => {
      window.removeEventListener('resize', updatePosition)
      window.removeEventListener('scroll', updatePosition, true)
    }
  }, [open])

  useEffect(() => {
    if (!reactionPickerOpen) {
      return
    }

    const onDocumentMouseDown = (e: MouseEvent | TouchEvent) => {
      const target = e.target
      if (target instanceof Node && refReactionPicker.current?.contains(target)) {
        return
      }
      setReactionPickerOpen(false)
    }

    document.addEventListener('mousedown', onDocumentMouseDown)
    document.addEventListener('touchstart', onDocumentMouseDown)

    return () => {
      document.removeEventListener('mousedown', onDocumentMouseDown)
      document.removeEventListener('touchstart', onDocumentMouseDown)
    }
  }, [reactionPickerOpen])

  useLayoutEffect(() => {
    if (!reactionPickerOpen) {
      return
    }

    const updatePosition = () => fitFloatingElementToViewport(refReactionPickerDropdown.current)
    updatePosition()
    window.addEventListener('resize', updatePosition)
    window.addEventListener('scroll', updatePosition, true)

    return () => {
      window.removeEventListener('resize', updatePosition)
      window.removeEventListener('scroll', updatePosition, true)
    }
  }, [reactionPickerOpen])

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
    navigateToForumPost(url)
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
    setIsEditing(false)
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

  const getPostShareUrl = useConstCallback(() => {
    const url = new URL(`/forum/t-${threadId}`, window.location.origin)
    url.hash = `post-${postId}`
    return url.toString()
  })

  const copyText = useConstCallback(async (text: string) => {
    if (navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(text)
        return
      } catch {
        // fallback below
      }
    }

    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.setAttribute('readonly', 'readonly')
    Object.assign(textarea.style, {
      position: 'fixed',
      left: '-9999px',
      top: '0',
    })
    document.body.appendChild(textarea)
    textarea.select()
    const copied = document.execCommand('copy')
    document.body.removeChild(textarea)

    if (!copied) {
      throw new Error('copy failed')
    }
  })

  const onShare = useConstCallback(async (e: React.MouseEvent<HTMLElement>) => {
    e.preventDefault()
    e.stopPropagation()

    try {
      await copyText(getPostShareUrl())
      setOpen(false)
    } catch {
      setDeleteError('Не удалось скопировать ссылку')
    }
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

  const canAddUserReaction = reactionState.canReact && reactionState.myCount < reactionState.limits.maxPerUser

  const findReactionSummary = useConstCallback((reactionId: number) => {
    return reactionState.reactions.find(item => item.reaction.id === reactionId) ?? null
  })

  const applyReactionState = useConstCallback((nextState: ForumPostReactionState) => {
    setReactionState(nextState)
  })

  const canAddReactionType = useConstCallback((reactionId: number) => {
    if (!canAddUserReaction) {
      return false
    }

    const isVisibleType = reactionState.reactions.some(item => item.reaction.id === reactionId)
    return isVisibleType || reactionState.reactions.length < reactionState.limits.maxPerPost
  })

  const addReaction = useConstCallback(async (reaction: ForumReaction) => {
    if (reactionLoading) {
      return
    }
    if (!reaction.isActive && !reactionState.canUseInactiveReactions) {
      setReactionError('Эта реакция сейчас недоступна')
      return
    }
    if (!canAddReactionType(reaction.id)) {
      setReactionError('Достигнут лимит типов реакций под этим сообщением')
      return
    }

    setReactionLoading(true)
    setReactionError('')
    try {
      const nextState = await addForumPostReaction(postId, reaction.id)
      applyReactionState(nextState)
      setReactionPickerOpen(false)
    } catch (e) {
      setReactionError(e.error || 'Ошибка связи с сервером')
    } finally {
      setReactionLoading(false)
    }
  })

  const removeReaction = useConstCallback(async (reactionId: number, userId?: number) => {
    if (reactionLoading) {
      return
    }

    setReactionLoading(true)
    setReactionError('')
    try {
      const nextState = await removeForumPostReaction(postId, reactionId, userId)
      applyReactionState(nextState)
    } catch (e) {
      setReactionError(e.error || 'Ошибка связи с сервером')
    } finally {
      setReactionLoading(false)
    }
  })

  const onToggleReaction = useConstCallback((e: React.MouseEvent<HTMLElement>, summary: ForumPostReactionSummary) => {
    e.preventDefault()
    e.stopPropagation()

    if (summary.me && reactionState.canRemoveOwnReactions) {
      removeReaction(summary.reaction.id)
      return
    }
    addReaction(summary.reaction)
  })

  const onPickReaction = useConstCallback((e: React.MouseEvent<HTMLElement>, reaction: ForumReaction) => {
    e.preventDefault()
    e.stopPropagation()

    const summary = findReactionSummary(reaction.id)
    if (summary?.me && reactionState.canRemoveOwnReactions) {
      removeReaction(reaction.id)
      setReactionPickerOpen(false)
      return
    }
    addReaction(reaction)
  })

  const onToggleReactionPicker = useConstCallback((e: React.MouseEvent<HTMLElement>) => {
    e.preventDefault()
    e.stopPropagation()

    setReactionPickerOpen(!reactionPickerOpen)
  })

  const onOpenReactionList = useConstCallback((e: React.MouseEvent<HTMLElement>) => {
    e.preventDefault()
    e.stopPropagation()

    setActiveReactionId(reactionState.reactions[0]?.reaction.id ?? null)
    setReactionListOpen(true)
    setOpen(false)
  })

  const onCloseReactionList = useConstCallback(() => {
    setReactionListOpen(false)
  })

  const onCloseReactionError = useConstCallback(() => {
    setReactionError('')
  })

  const onRemoveReactionUser = useConstCallback((e: React.MouseEvent<HTMLElement>, summary: ForumPostReactionSummary, reactionUser: UserData) => {
    e.preventDefault()
    e.stopPropagation()

    if (reactionUser.id === undefined || !reactionState.canModerateReactions) {
      return
    }
    removeReaction(summary.reaction.id, reactionUser.id)
  })

  const onRemoveReactionType = useConstCallback(async (e: React.MouseEvent<HTMLElement>, summary: ForumPostReactionSummary) => {
    e.preventDefault()
    e.stopPropagation()

    if (reactionLoading || !reactionState.canModerateReactions) {
      return
    }

    setReactionLoading(true)
    setReactionError('')
    try {
      const nextState = await removeAllForumPostReactions(postId, summary.reaction.id)
      applyReactionState(nextState)
      setActiveReactionId(nextState.reactions[0]?.reaction.id ?? null)
    } catch (e) {
      setReactionError(e.error || 'Ошибка связи с сервером')
    } finally {
      setReactionLoading(false)
    }
  })

  const onSelectReactionTab = useConstCallback((e: React.MouseEvent<HTMLElement>, summary: ForumPostReactionSummary) => {
    e.preventDefault()
    e.stopPropagation()

    setActiveReactionId(summary.reaction.id)
  })

  const renderReactionImage = useConstCallback((reaction: ForumReaction, className: string) => {
    if (reaction.imageUrl) {
      return <img className={className} src={reaction.imageUrl} alt={reaction.name} />
    }
    return <span className={`${className} forum-reaction-image-fallback`}>{reaction.name.slice(0, 1)}</span>
  })

  const renderReactionPicker = useConstCallback(() => {
    if (!reactionPickerOpen) {
      return null
    }

    return (
      <div className="forum-reaction-picker" ref={r => (refReactionPickerDropdown.current = r ?? undefined)}>
        {reactionState.availableReactions.map(reaction => {
          const summary = findReactionSummary(reaction.id)
          const selected = summary?.me === true
          const disabled =
            reactionLoading ||
            (selected && !reactionState.canRemoveOwnReactions) ||
            (!selected && (!canAddReactionType(reaction.id) || (!reaction.isActive && !reactionState.canUseInactiveReactions)))

          return (
            <button
              className={`forum-reaction-picker-item ${selected ? 'is-selected' : ''} ${reactionLoading ? 'is-loading' : ''}`}
              disabled={disabled}
              key={reaction.id}
              onClick={e => onPickReaction(e, reaction)}
              title={reaction.name}
              type="button"
            >
              {renderReactionImage(reaction, 'forum-reaction-picker-image')}
            </button>
          )
        })}
        {reactionState.availableReactions.length === 0 && <div className="forum-reaction-picker-empty">Нет доступных реакций</div>}
      </div>
    )
  })

  const renderReactions = useConstCallback(() => {
    const showPickerButton = reactionState.canReact && reactionState.availableReactions.length > 0
    if (!reactionState.reactions.length && !showPickerButton) {
      return null
    }

    return (
      <div className="forum-reactions">
        <div className="forum-reaction-list">
          {reactionState.reactions.map(summary => {
            const canToggle = summary.me
              ? reactionState.canRemoveOwnReactions
              : (summary.reaction.isActive || reactionState.canUseInactiveReactions) && canAddReactionType(summary.reaction.id)
            const chipTitle = summary.me
              ? `Убрать реакцию "${summary.reaction.name}"`
              : summary.reaction.isActive || reactionState.canUseInactiveReactions
                ? `Поставить реакцию "${summary.reaction.name}"`
                : `Реакция "${summary.reaction.name}" сейчас недоступна`

            return (
              <span
                className={`forum-reaction-chip ${!summary.reaction.isActive ? 'is-inactive' : ''}`}
                key={summary.reaction.id}
              >
                <button
                  className={`forum-reaction-chip-main ${reactionLoading ? 'is-loading' : ''}`}
                  disabled={reactionLoading || !canToggle}
                  onClick={e => onToggleReaction(e, summary)}
                  title={chipTitle}
                  type="button"
                >
                  {renderReactionImage(summary.reaction, 'forum-reaction-chip-image')}
                  <span className={`forum-reaction-chip-count ${summary.me ? 'is-mine' : ''}`}>{summary.count}</span>
                </button>
              </span>
            )
          })}
          {showPickerButton && (
            <span className="forum-reaction-picker-wrap" ref={r => (refReactionPicker.current = r ?? undefined)}>
              <button
                className={`forum-reaction-add ${reactionLoading ? 'is-loading' : ''}`}
                disabled={reactionLoading}
                onClick={onToggleReactionPicker}
                title="Добавить реакцию"
                type="button"
              >
                <i className="far fa-smile" />
              </button>
              {renderReactionPicker()}
            </span>
          )}
        </div>
      </div>
    )
  })

  const renderReactionList = useConstCallback(() => {
    if (!reactionListOpen) {
      return null
    }

    const activeSummary =
      reactionState.reactions.find(summary => summary.reaction.id === activeReactionId) ?? reactionState.reactions[0] ?? null

    return (
      <WikidotModal buttons={[{ title: 'Закрыть', onClick: onCloseReactionList }]} isLoading={reactionLoading}>
        <div className="forum-reaction-details">
          <h2>Реакции</h2>
          {reactionState.reactions.length > 0 ? (
            <div className="forum-reaction-tabs-layout">
              <div className="forum-reaction-tabs" role="tablist" aria-label="Реакции к сообщению">
                {reactionState.reactions.map(summary => {
                  const isActive = activeSummary?.reaction.id === summary.reaction.id

                  return (
                    <button
                      aria-selected={isActive}
                      className={`forum-reaction-tab ${isActive ? 'is-active' : ''}`}
                      key={summary.reaction.id}
                      onClick={e => onSelectReactionTab(e, summary)}
                      role="tab"
                      title={summary.reaction.name}
                      type="button"
                    >
                      {renderReactionImage(summary.reaction, 'forum-reaction-details-image')}
                      <span>{summary.reaction.name}</span>
                      <strong>{summary.count}</strong>
                    </button>
                  )
                })}
              </div>
              {activeSummary && (
                <div className="forum-reaction-tab-panel" role="tabpanel">
                  <div className="forum-reaction-panel-head">
                    <div className="forum-reaction-panel-title">
                      {renderReactionImage(activeSummary.reaction, 'forum-reaction-details-image')}
                      <span>{activeSummary.reaction.name}</span>
                      <strong>{activeSummary.count}</strong>
                    </div>
                    {reactionState.canModerateReactions && (
                      <a href="#" className="btn btn-danger btn-xs" onClick={e => onRemoveReactionType(e, activeSummary)}>
                        <i className="fas fa-times" /> Удалить всех
                      </a>
                    )}
                  </div>
                  <div className="forum-reaction-user-list">
                    {activeSummary.users.map((reactionUser, index) => (
                      <div className="forum-reaction-user-row" key={`${activeSummary.reaction.id}-${reactionUser.id ?? index}`}>
                        <div className="forum-reaction-user">
                          <UserView data={reactionUser} />
                        </div>
                        {reactionState.canModerateReactions && reactionUser.id !== undefined && (
                          <a href="#" className="btn btn-default btn-xs" onClick={e => onRemoveReactionUser(e, activeSummary, reactionUser)}>
                            <i className="fas fa-times" /> Удалить
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="forum-reaction-table-empty">Под сообщением пока нет реакций.</p>
          )}
        </div>
      </WikidotModal>
    )
  })

  const canOpenReactionList = reactionState.reactions.length > 0
  const canShare = true
  const hasPostOptions = canShare || canEdit || canDelete || canOpenReactionList
  const postMenu = hasPostOptions ? (
    <div className="forum-post-menu" ref={r => (refPostMenu.current = r ?? undefined)}>
      <button
        aria-expanded={open}
        aria-haspopup="true"
        aria-label="Опции"
        className="forum-post-menu-button"
        onClick={onToggle}
        title="Опции"
        type="button"
      >
        <i className="fas fa-ellipsis-v" />
      </button>
      {open && (
        <div className="forum-post-menu-dropdown" ref={r => (refPostMenuDropdown.current = r ?? undefined)} role="menu">
          {canShare && (
            <button onClick={onShare} role="menuitem" type="button">
              Поделиться
            </button>
          )}
          {canOpenReactionList && (
            <a href="#" onClick={onOpenReactionList} role="menuitem">
              Реакции
            </a>
          )}
          {canEdit && (
            <a href="#" onClick={onEdit} role="menuitem">
              Редактировать
            </a>
          )}
          {canDelete && (
            <a href="#" onClick={onDelete} role="menuitem">
              Удалить
            </a>
          )}
        </div>
      )}
    </div>
  ) : null
  const replyButton =
    canReply && !isReplying ? (
      <a aria-label="Ответить" className="forum-post-reply-button" href="#" onClick={onReply} title="Ответить">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path d="M268.2 82.4C280.2 87.4 288 99 288 112L288 192L400 192C497.2 192 576 270.8 576 368C576 481.3 494.5 531.9 475.8 542.1C473.3 543.5 470.5 544 467.7 544C456.8 544 448 535.1 448 524.3C448 516.8 452.3 509.9 457.8 504.8C467.2 496 480 478.4 480 448.1C480 395.1 437 352.1 384 352.1L288 352.1L288 432.1C288 445 280.2 456.7 268.2 461.7C256.2 466.7 242.5 463.9 233.3 454.8L73.3 294.8C60.8 282.3 60.8 262 73.3 249.5L233.3 89.5C242.5 80.3 256.2 77.6 268.2 82.6z"/></svg>
      </a>
    ) : null
  const reactionControls = renderReactions()

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
      {reactionError && (
        <WikidotModal buttons={[{ title: 'Закрыть', onClick: onCloseReactionError }]} isError>
          <p>
            <strong>Ошибка:</strong> {reactionError}
          </p>
        </WikidotModal>
      )}
      {renderReactionList()}
      {(replyButton || reactionControls) && (
        <div className="forum-post-actions">
          {replyButton}
          {reactionControls}
        </div>
      )}
      {menuPortal ? postMenu && ReactDOM.createPortal(postMenu, menuPortal) : postMenu}
      {isReplying && (
        <div className="post-container">
          <ForumPostEditor
            isNew
            useAdvancedEditor={false}
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
          useAdvancedEditor={false}
          onClose={onEditClose}
          onSubmit={onEditSubmit}
          onPreview={onEditPreview}
        />
      )}
    </>
  )
}

export default ForumPostOptions
