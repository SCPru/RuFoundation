import * as React from 'react'
import { matchPath, useNavigate } from 'react-router-dom'
import Page from '~reactive/containers/page'
import NotificationsInfiniteScroll from '~reactive/pages/notifications/NotificationsInfiniteScroll'
import { Paths } from '~reactive/paths'
import * as Styled from './Notifications.styles'

const Notifications: React.FC = () => {
  const showUnread = Boolean(
    matchPath(`/-${Paths.notifications}`, window.location.pathname) || matchPath(`/-${Paths.notificationsUnread}`, window.location.pathname),
  )
  const navigate = useNavigate()

  console.log('showUnread', showUnread)

  return (
    <Page>
      <Styled.FilterContainer>
        <Styled.RadioLabel checked={showUnread}>
          <Styled.RadioInput type="radio" name="filter" checked={showUnread} onChange={() => navigate(Paths.notificationsUnread)} />
          Непрочитанные
        </Styled.RadioLabel>
        <Styled.RadioLabel checked={!showUnread}>
          <Styled.RadioInput type="radio" name="filter" checked={!showUnread} onChange={() => navigate(Paths.notificationsAll)} />
          Все
        </Styled.RadioLabel>
      </Styled.FilterContainer>
      <NotificationsInfiniteScroll batchSize={10} showUnread={showUnread} />
    </Page>
  )
}

export default Notifications
