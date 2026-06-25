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
  pinForumPost,
  removeAllForumPostReactions,
  removeForumPostReaction,
  updateForumPost,
} from '../api/forum'
import { UserData } from '../api/user'
import ForumPostEditor, { ForumPostPreviewData, ForumPostSubmissionData } from '../forum/forum-post-editor'
import ForumPostPreview from '../forum/forum-post-preview'
import useConstCallback from '../util/const-callback'
import formatDate from '../util/date-format'
import Tooltip from '../util/tooltip'
import UserView from '../util/user-view'
import WikidotModal from '../util/wikidot-modal'

interface Props {
  user: UserData
  threadId: number
  threadName: string
  postId: number
  postName: string
  replyCount?: number
  replyCountLabel?: string
  canReply?: boolean
  canEdit?: boolean
  canDelete?: boolean
  canPin?: boolean
  isPinned?: boolean
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

function getUserLabel(user?: UserData) {
  if (!user) {
    return 'system'
  }
  if (user.type === 'system') {
    return 'system'
  }
  if (user.type === 'anonymous') {
    return 'Anonymous User'
  }
  return user.name || user.username || 'system'
}

const ForumPostOptions: React.FC<Props> = ({
  user,
  threadId,
  postId,
  postName,
  replyCount = 0,
  replyCountLabel = '',
  canReply,
  canEdit,
  canDelete,
  canPin,
  isPinned,
  canReact,
  canRemoveOwnReactions,
  canModerateReactions,
  canUseInactiveReactions,
  availableReactions = [],
  reactions = [],
  reactionLimits = { maxPerUser: 0, maxPerPost: 0 },
  reactionTotalCount,
  myReactionCount,
  hasRevisions: initialHasRevisions,
  lastRevisionDate: initialLastRevisionDate,
  lastRevisionAuthor: initialLastRevisionAuthor,
  preferences,
}) => {
  const [isEditing, setIsEditing] = useState(false)
  const [isReplying, setIsReplying] = useState(false)
  const [open, setOpen] = useState(false)
  const [originalPreviewTitle, setOriginalPreviewTitle] = useState('')
  const [originalPreviewContent, setOriginalPreviewContent] = useState('')
  const [deleteError, setDeleteError] = useState('')
  const [postPinned, setPostPinned] = useState(isPinned === true)
  const [pinLoading, setPinLoading] = useState(false)
  const [revisionsOpen, setRevisionsOpen] = useState(false)
  const [currentRevision, setCurrentRevision] = useState('')
  const [revisions, setRevisions] = useState<Array<ForumPostVersion>>([])
  const [hasVisibleRevisions, setHasVisibleRevisions] = useState(initialHasRevisions === true)
  const [revisionDate, setRevisionDate] = useState(initialLastRevisionDate)
  const [revisionAuthor, setRevisionAuthor] = useState<UserData | undefined>(initialLastRevisionAuthor)
  const [repliesCollapsed, setRepliesCollapsed] = useState(false)
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
  const [editMetaPortal, setEditMetaPortal] = useState<HTMLElement | null>(null)

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
    const infoDate = longPost.querySelector('.head .info .odate') as HTMLElement | null
    const menuSlot = document.createElement('div')
    menuSlot.className = 'forum-post-menu-slot'
    const editMetaSlot = document.createElement('span')
    editMetaSlot.className = 'forum-post-edit-meta-slot'
    if (head) {
      head.insertBefore(menuSlot, head.firstChild)
      setMenuPortal(menuSlot)
    }
    if (infoDate) {
      infoDate.insertAdjacentElement('afterend', editMetaSlot)
      setEditMetaPortal(editMetaSlot)
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
      if (editMetaSlot.parentElement) {
        editMetaSlot.parentElement.removeChild(editMetaSlot)
      }
    }
  }, [])

  useLayoutEffect(() => {
    const postContainer = refSelf.current?.closest('.post-container') as HTMLElement | null
    if (!postContainer || !replyCount) {
      return
    }

    postContainer.classList.toggle('forum-post-replies-collapsed', repliesCollapsed)

    return () => {
      postContainer.classList.remove('forum-post-replies-collapsed')
    }
  }, [replyCount, repliesCollapsed])

  useLayoutEffect(() => {
    const post = refSelf.current?.closest('.post') as HTMLElement | null
    const head = post?.querySelector(':scope > .long > .head') as HTMLElement | null
    post?.classList.toggle('is-pinned', postPinned)
    head?.classList.toggle('pinned-post', postPinned)
  }, [postPinned])

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
    const nextHasRevisions = result.hasRevisions ?? result.createdAt !== result.updatedAt
    setHasVisibleRevisions(nextHasRevisions)
    setRevisionDate(nextHasRevisions ? result.lastRevisionDate || result.updatedAt : undefined)
    setRevisionAuthor(nextHasRevisions ? result.lastRevisionAuthor : undefined)
    setRevisions([])
    setRevisionsOpen(false)
    setCurrentRevision('')
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

  const onTogglePin = useConstCallback(async (e: React.MouseEvent<HTMLElement>) => {
    e.preventDefault()
    e.stopPropagation()

    if (pinLoading) {
      return
    }

    const nextPinned = !postPinned
    setPinLoading(true)
    try {
      const result = await pinForumPost(postId, nextPinned)
      setPostPinned(result.isPinned)
      setOpen(false)
      window.dispatchEvent(new CustomEvent('forum:post-pin-changed', { detail: result }))
    } catch (e) {
      setDeleteError(e.error || 'Ошибка связи с сервером')
    } finally {
      setPinLoading(false)
    }
  })

  const onToggle = useConstCallback(e => {
    e.preventDefault()
    e.stopPropagation()

    setOpen(!open)
  })

  const onToggleReplies = useConstCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault()
    e.stopPropagation()

    setRepliesCollapsed(value => !value)
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
        setOpen(false)
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
            <Tooltip content={reaction.name} key={reaction.id}>
              <span className="forum-reaction-tooltip-target">
                <button
                  className={`forum-reaction-picker-item ${selected ? 'is-selected' : ''} ${reactionLoading ? 'is-loading' : ''}`}
                  disabled={disabled}
                  onClick={e => onPickReaction(e, reaction)}
                  type="button"
                >
                  {renderReactionImage(reaction, 'forum-reaction-picker-image')}
                </button>
              </span>
            </Tooltip>
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
              <span className={`forum-reaction-chip ${!summary.reaction.isActive ? 'is-inactive' : ''}`} key={summary.reaction.id}>
                <Tooltip content={chipTitle}>
                  <span className="forum-reaction-tooltip-target">
                    <button
                      className={`forum-reaction-chip-main ${reactionLoading ? 'is-loading' : ''}`}
                      disabled={reactionLoading || !canToggle}
                      onClick={e => onToggleReaction(e, summary)}
                      type="button"
                    >
                      {renderReactionImage(summary.reaction, 'forum-reaction-chip-image')}
                      <span className={`forum-reaction-chip-count ${summary.me ? 'is-mine' : ''}`}>{summary.count}</span>
                    </button>
                  </span>
                </Tooltip>
              </span>
            )
          })}
          {showPickerButton && (
            <span className="forum-reaction-picker-wrap" ref={r => (refReactionPicker.current = r ?? undefined)}>
              <Tooltip content="Добавить реакцию">
                <span className="forum-reaction-tooltip-target">
                  <button
                    className={`forum-reaction-add ${reactionLoading ? 'is-loading' : ''}`}
                    disabled={reactionLoading}
                    onClick={onToggleReactionPicker}
                    type="button"
                  >
                    <i className="far fa-smile" />
                  </button>
                </span>
              </Tooltip>
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
                    <Tooltip content={summary.reaction.name} key={summary.reaction.id}>
                      <button
                        aria-selected={isActive}
                        className={`forum-reaction-tab ${isActive ? 'is-active' : ''}`}
                        onClick={e => onSelectReactionTab(e, summary)}
                        role="tab"
                        type="button"
                      >
                        {renderReactionImage(summary.reaction, 'forum-reaction-details-image')}
                        <span>{summary.reaction.name}</span>
                        <strong>{summary.count}</strong>
                      </button>
                    </Tooltip>
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
  const hasPostOptions = canShare || canEdit || canDelete || canPin || canOpenReactionList || hasVisibleRevisions
  const revisionDateLabel = revisionDate ? formatDate(new Date(revisionDate)) : ''
  const revisionAuthorLabel = getUserLabel(revisionAuthor)
  const editMeta =
    hasVisibleRevisions && revisionDate && revisionAuthor ? (
      <Tooltip
        className="w-tooltip-stack"
        content={
          <>
            <span className="w-tooltip-title">Последнее редактирование</span>
            <span>
              Дата:{' '}
              <span className="odate" style={{ display: 'inline' }}>
                {revisionDateLabel}
              </span>
            </span>
            <span>
              Пользователь: <UserView data={revisionAuthor} />
            </span>
          </>
        }
      >
        <span aria-label={`Последнее редактирование: ${revisionDateLabel}, ${revisionAuthorLabel}`} className="forum-post-edit-meta" tabIndex={0}>
          <i aria-hidden="true" className="fas fa-pen" />
        </span>
      </Tooltip>
    ) : null
  const postMenu = hasPostOptions ? (
    <div className="forum-post-menu" ref={r => (refPostMenu.current = r ?? undefined)}>
      <Tooltip content="Опции">
        <button aria-expanded={open} aria-haspopup="true" aria-label="Опции" className="forum-post-menu-button" onClick={onToggle} type="button">
          <i className="fas fa-ellipsis-v" />
        </button>
      </Tooltip>
      {open && (
        <div className="forum-post-menu-dropdown" ref={r => (refPostMenuDropdown.current = r ?? undefined)} role="menu">
          {canShare && (
            <button onClick={onShare} role="menuitem" type="button">
              Поделиться
            </button>
          )}
          {canPin && (
            <button disabled={pinLoading} onClick={onTogglePin} role="menuitem" type="button">
              {postPinned ? 'Открепить' : 'Закрепить'}
            </button>
          )}
          {canOpenReactionList && (
            <a href="#" onClick={onOpenReactionList} role="menuitem">
              Реакции
            </a>
          )}
          {hasVisibleRevisions && (
            <a href="#" onClick={onOpenRevisions} role="menuitem">
              История правок
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
  const pinIndicator = postPinned ? (
    <Tooltip content="Закрепленное сообщение">
      <span aria-label="Закрепленное сообщение" className="forum-post-pin-indicator" tabIndex={0}>
        <i aria-hidden="true" className="fas fa-thumbtack" />
      </span>
    </Tooltip>
  ) : null
  const menuContent =
    pinIndicator || postMenu ? (
      <>
        {pinIndicator}
        {postMenu}
      </>
    ) : null
  const replyButton =
    canReply && !isReplying ? (
      <Tooltip content="Ответить">
        <a aria-label="Ответить" className="forum-post-reply-button" href="#" onClick={onReply}>
          <i className="fas fa-reply"></i>
        </a>
      </Tooltip>
    ) : null
  const repliesToggle =
    replyCount > 0 && replyCountLabel ? (
      <button
        aria-expanded={!repliesCollapsed}
        aria-label={repliesCollapsed ? `Развернуть ${replyCountLabel}` : `Свернуть ${replyCountLabel}`}
        className={`forum-post-replies-toggle ${repliesCollapsed ? 'is-collapsed' : ''}`}
        onClick={onToggleReplies}
        type="button"
      >
        <span>{replyCountLabel}</span>
        <i className={`fas ${repliesCollapsed ? 'fa-angle-right' : 'fa-angle-down'}`} aria-hidden="true" />
      </button>
    ) : null
  const rightActions =
    replyButton || repliesToggle ? (
      <div className="forum-post-right-actions">
        {repliesToggle}
        {replyButton}
      </div>
    ) : null
  const reactionControls = renderReactions()

  return (
    <>
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
      {(rightActions || reactionControls) && (
        <div className="forum-post-actions">
          {rightActions}
          {reactionControls}
        </div>
      )}
      {menuPortal ? menuContent && ReactDOM.createPortal(menuContent, menuPortal) : menuContent}
      {editMetaPortal ? editMeta && ReactDOM.createPortal(editMeta, editMetaPortal) : null}
      {isReplying && (
        <div className="post-container">
          <ForumPostEditor
            isNew
            useAdvancedEditor={false}
            onClose={onReplyClose}
            onSubmit={onReplySubmit}
            onPreview={onReplyPreview}
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
