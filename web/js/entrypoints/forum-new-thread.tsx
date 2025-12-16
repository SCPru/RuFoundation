import * as React from 'react'
import { useState } from 'react'
import { createForumThread, ForumNewThreadRequest } from '../api/forum'
import { UserData } from '../api/user'
import ForumPostEditor, { ForumPostPreviewData, ForumPostSubmissionData } from '../forum/forum-post-editor'
import ForumPostPreview from '../forum/forum-post-preview'
import useConstCallback from '../util/const-callback'

interface Props {
  user: UserData
  categoryId: number
  cancelUrl?: string
  preferences?: { [key: string]: any }
}

const ForumNewThread: React.FC<Props> = ({ user, categoryId, cancelUrl, preferences }) => {
  const [preview, setPreview] = useState<ForumPostPreviewData>()

  const onClose = useConstCallback(async () => {
    window.location.href = cancelUrl || '/forum/start'
  })

  const onSubmit = useConstCallback(async (input: ForumPostSubmissionData) => {
    const request: ForumNewThreadRequest = {
      categoryId,
      name: input.name,
      description: input.description,
      source: input.source,
    }
    const { url } = await createForumThread(request)
    window.location.href = url
  })

  const onPreview = useConstCallback((input: ForumPostPreviewData) => {
    setPreview(input)
  })

  return (
    <>
      {preview && <ForumPostPreview preview={preview} user={user} />}
      <ForumPostEditor
        isNew
        isThread
        useAdvancedEditor={preferences?.['qol__advanced_source_editor_enabled'] === true}
        onClose={onClose}
        onSubmit={onSubmit}
        onPreview={onPreview}
      />
    </>
  )
}

export default ForumNewThread
