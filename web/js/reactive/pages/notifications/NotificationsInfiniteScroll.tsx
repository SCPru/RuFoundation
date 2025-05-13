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
  isForceUpdate?: () => boolean
}

const NotificationsInfiniteScroll: React.FC<Props> = ({ batchSize, showUnread, isForceUpdate }) => {
  const [items, setItems] = useState<INotification[]>([])
  const [cursor, setCursor] = useState(-1)
  const [hasMore, setHasMore] = useState(true)
  const [isFetching, setIsFetching] = useState(false)
  const [isWaitingFetch, setIsWaitingFetch] = useState(false)

  useEffect(() => {
    if (!isForceUpdate) return
    if (isForceUpdate()) {
      setIsFetching(false)
      setHasMore(true)
      setCursor(-1)
      setItems([])
    }
  })

  useEffect(() => {
    if (!isFetching && isWaitingFetch)
      loadMore()
  }, [isFetching])

  const loadMore = useConstCallback(async () => {
    while (isFetching) {
      setIsWaitingFetch(true)
      return
    }

    setIsFetching(true)
    try {
      const resp = await getNotifications(cursor, batchSize, showUnread, true)
      setItems(prev => [...prev, ...resp.notifications])
      setCursor(resp.cursor)

      if (resp.notifications.length < batchSize || resp.cursor === -1) {
        setIsWaitingFetch(false)
        setHasMore(false)
      }
    } catch (e: any) {
      setHasMore(false)
      console.error('Failed to fetch more notifications', e)
    } finally {
      setIsFetching(false)
    }
  })

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
