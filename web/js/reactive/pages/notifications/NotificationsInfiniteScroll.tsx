import * as React from 'react'
import { useEffect, useState } from 'react'
import InfiniteScroll from 'react-infinite-scroller'
import { getNotifications, Notification as INotification } from '~api/notifications'
import useConstCallback from '~util/const-callback'
import Loader from '~util/loader'
import Notification from './Notification'
import * as Styled from './Notifications.styles'

interface Props {
  batchSize: number
  showUnread: boolean
}

const NotificationsInfiniteScroll: React.FC<Props> = ({ batchSize, showUnread }) => {
  const [items, setItems] = useState<INotification[]>([])
  const [cursor, setCursor] = useState(-1)
  const [hasMore, setHasMore] = useState(true)
  const [isFetching, setIsFetching] = useState(false)

  const loadMore = useConstCallback(async () => {
    if (isFetching) return

    setIsFetching(true)
    try {
      const resp = await getNotifications(cursor, batchSize, showUnread, true)
      setItems(prev => [...prev, ...resp.notifications])
      setCursor(resp.cursor)

      if (resp.notifications.length < batchSize || resp.cursor === -1) setHasMore(false)
    } catch (e: any) {
      setHasMore(false)
      console.error('Failed to fetch more notifications', e)
    } finally {
      setIsFetching(false)
    }
  })

  useEffect(() => {
    setIsFetching(false)
    setItems([])
    setCursor(-1)
    setHasMore(true)
  }, [showUnread])

  const loader = (
    <Styled.LoaderContainer key={0}>
      <Loader />
    </Styled.LoaderContainer>
  )

  return (
    <>
      <InfiniteScroll loadMore={loadMore} hasMore={hasMore} loader={loader} initialLoad={true}>
        <Styled.List>
          {items.map((item, n) => (
            <Notification notification={item} key={n} />
          ))}
        </Styled.List>
      </InfiniteScroll>
      {!hasMore && items.length === 0 && <Styled.EmptyMessage>Уведомлений пока нет :(</Styled.EmptyMessage>}
    </>
  )
}

export default NotificationsInfiniteScroll
