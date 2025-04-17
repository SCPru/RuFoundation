import React, { useMemo } from 'react'
import { ArticleLogEntry } from '~api/articles'
import { Notification as INotification } from '~api/notifications'
import { renderArticleHistoryComment, renderArticleHistoryFlags } from '~articles/article-history'
import formatDate from '~util/date-format'
import UserView from '~util/user-view'
import * as Styled from './Notification.styles'

interface Props {
  notification: INotification
}

const Notification: React.FC<Props> = ({ notification }) => {
  const notificationContent = useMemo(() => {
    if (notification.type === 'generic') {
      return (
        <>
          <div dangerouslySetInnerHTML={{ __html: notification.title }}></div>
          <div dangerouslySetInnerHTML={{ __html: notification.message }}></div>
        </>
      )
    } else if (notification.type === 'new_post_reply' || notification.type === 'new_thread_post') {
      return (
        <>
          <Styled.TypeName>{notification.type === 'new_post_reply' ? 'Ответ на ваше сообщение' : 'Новое сообщение форума'}</Styled.TypeName>
          <Styled.PostFrom>
            От <UserView data={notification.author} /> в теме <a href={notification.section.url}>{notification.section.name}</a> &raquo;{' '}
            <a href={notification.category.url}>{notification.category.name}</a> &raquo;{' '}
            <a href={notification.thread.url}>{notification.thread.name}</a>
          </Styled.PostFrom>
          <Styled.PostName>
            <a href={notification.post.url}>{notification.post.name || 'Перейти к сообщению'}</a>
          </Styled.PostName>
          <Styled.PostContent>
            <div dangerouslySetInnerHTML={{ __html: notification.message }} />
          </Styled.PostContent>
        </>
      )
    } else if (notification.type === 'new_article_revision') {
      const logEntry: ArticleLogEntry = {
        comment: notification.comment,
        createdAt: notification.created_at,
        meta: notification.rev_meta,
        revNumber: notification.rev_number,
        type: notification.rev_type,
        user: notification.user,
      }

      const pageName = notification.article.pageId.indexOf(':')
        ? `${notification.article.pageId.split(':')[0]}: ${notification.article.title}`
        : notification.article.title
      const comment = renderArticleHistoryComment(logEntry)

      return (
        <>
          <Styled.TypeName>Новая правка на отслеживаемой странице</Styled.TypeName>
          <Styled.RevisionFields>
            <Styled.RevisionArticle>
              <a href={`/${notification.article.pageId}`}>{pageName}</a>
            </Styled.RevisionArticle>
            <Styled.RevisionFlags>{renderArticleHistoryFlags(logEntry)}</Styled.RevisionFlags>
            <Styled.RevisionNumber>(рев. {notification.rev_number})</Styled.RevisionNumber>
            <Styled.RevisionUser>
              <UserView data={notification.user} />
            </Styled.RevisionUser>
          </Styled.RevisionFields>
          <Styled.RevisionComment>
            {comment && (
              <>
                <Styled.RevisionCommentCaption>Комментарий:</Styled.RevisionCommentCaption> {comment}
              </>
            )}
          </Styled.RevisionComment>
        </>
      )
    } else {
      return 'Ошибка отрисовки уведомления'
    }
  }, [notification])

  return (
    <Styled.Container>
      <Styled.NotificationDate>{formatDate(new Date(notification.created_at))}</Styled.NotificationDate>
      {notificationContent}
    </Styled.Container>
  )
}

export default Notification
