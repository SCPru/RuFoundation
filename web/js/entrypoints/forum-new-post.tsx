import * as React from 'react'
import { useState } from 'react'
import { createForumPost, ForumNewPostRequest } from '../api/forum'
import { UserData } from '../api/user'
import ForumPostEditor, { ForumPostPreviewData, ForumPostSubmissionData } from '../forum/forum-post-editor'
import ForumPostPreview from '../forum/forum-post-preview'
import useConstCallback from '../util/const-callback'

interface Props {
  user: UserData
  threadId: number
  threadName: string
  preferences?: { [key: string]: any }
}

function navigateToForumPost(url: string) {
  const detail = { url, handled: false }
  window.dispatchEvent(new CustomEvent('forum:post-created', { detail }))
  if (!detail.handled) {
    window.location.href = url
  }
}

const ForumNewPost: React.FC<Props> = ({ user, threadId, preferences }) => {
  const [preview, setPreview] = useState<ForumPostPreviewData>()
  const [open, setOpen] = useState(false)

  const onOpen = useConstCallback(e => {
    e.preventDefault()
    e.stopPropagation()
    const closeCurrent = (window as any)._closePostEditor
    if (closeCurrent) {
      closeCurrent()
    }
    setOpen(true)
    setPreview(undefined)
  })

  const onClose = useConstCallback(async () => {
    setOpen(false)
  })

  const onSubmit = useConstCallback(async (input: ForumPostSubmissionData) => {
    const request: ForumNewPostRequest = {
      threadId,
      name: input.name,
      source: input.source,
    }
    const { url } = await createForumPost(request)
    setOpen(false)
    navigateToForumPost(url)
  })

  const onPreview = useConstCallback((input: ForumPostPreviewData) => {
    setPreview(input)
  })

  return !open ? (
    <div className="new-post">
      <a href="#" onClick={onOpen}>
        Новое сообщение
      </a>
    </div>
  ) : (
    <>
      {preview && <ForumPostPreview preview={preview} user={user} />}
      <ForumPostEditor
        isNew
        useAdvancedEditor={false}
        onClose={onClose}
        onSubmit={onSubmit}
        onPreview={onPreview}
      />
    </>
  )
}

export default ForumNewPost
