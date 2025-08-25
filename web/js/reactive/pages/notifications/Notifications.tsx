import * as React from 'react'
import { useState } from 'react'
import { matchPath, useNavigate } from 'react-router-dom'
import { ProfilePage } from '~reactive/containers/page'
import NotificationsInfiniteScroll from '~reactive/pages/notifications/NotificationsInfiniteScroll'
import { Paths } from '~reactive/paths'
import useConstCallback from '../../../util/const-callback'
import * as Styled from './Notifications.styles'

const Notifications: React.FC = () => {
  const [forceUpdate, setForceUpdate] = useState<boolean>(false)
  const showUnread = Boolean(
    matchPath(`/-${Paths.notifications}`, window.location.pathname) || matchPath(`/-${Paths.notificationsUnread}`, window.location.pathname),
  )
  const navigate = useNavigate()

  const isForceUpdate = useConstCallback(() => {
    setForceUpdate(false)
    return forceUpdate
  })

  const onChecked = useConstCallback(dest => {
    navigate(dest)
    setForceUpdate(true)
  })

  return (
    <ProfilePage>
      <Styled.FilterContainer>
        <Styled.RadioLabel checked={showUnread}>
          <Styled.RadioInput type="radio" name="filter" checked={showUnread} onChange={() => onChecked(Paths.notificationsUnread)} />
          Непрочитанные
        </Styled.RadioLabel>
        <Styled.RadioLabel checked={!showUnread}>
          <Styled.RadioInput type="radio" name="filter" checked={!showUnread} onChange={() => onChecked(Paths.notificationsAll)} />
          Все
        </Styled.RadioLabel>
      </Styled.FilterContainer>
      <NotificationsInfiniteScroll key={`tab-${showUnread}`} batchSize={10} showUnread={showUnread} isForceUpdate={isForceUpdate} />
    </ProfilePage>
  )
}

export default Notifications
