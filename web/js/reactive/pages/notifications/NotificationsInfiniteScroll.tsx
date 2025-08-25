import * as React from 'react'
import { useEffect, useRef, useState } from 'react'
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
  const loaderRef = useRef<HTMLDivElement | null>(null)
  const [isLoaderVisible, setIsLoaderVisible] = useState(false)

  useEffect(() => {
    if (!isForceUpdate) return
    if (isForceUpdate()) {
      setIsFetching(false)
      setHasMore(true)
      setCursor(-1)
      setItems([])
    }
  })

  const handleVisibleChange = useConstCallback((newVisible: boolean) => {
    if (isLoaderVisible !== newVisible) {
      setIsLoaderVisible(newVisible)
    }
  })

  useEffect(() => {
    if (isLoaderVisible && !isFetching && hasMore) {
      loadMore()
    }
  }, [isFetching, isLoaderVisible])

  const loadMore = useConstCallback(async () => {
    while (isFetching) {
      return
    }

    setIsFetching(true)
    try {
      const resp = await getNotifications(cursor, batchSize, showUnread, true)
      setItems(prev => [...prev, ...resp.notifications])
      setCursor(resp.cursor)

      if (resp.notifications.length < batchSize || resp.cursor === -1) {
        setHasMore(false)
      }
    } catch (e: any) {
      setHasMore(false)
      console.error('Failed to fetch more notifications', e)
    } finally {
      setIsFetching(false)
    }
  })

  useEffect(() => {
    const loader = loaderRef.current
    if (!loader) {
      return undefined
    }

    const observer = new IntersectionObserver(entries => {
      console.log('visibility change', entries)
      const newVisible = entries.some(x => x.isIntersecting && x.intersectionRatio > 0)
      handleVisibleChange(newVisible)
    })

    observer.observe(loader)

    return () => {
      observer.unobserve(loader)
    }
  }, [loaderRef.current])

  return (
    <>
      <Styled.List>
        {items.map((item, n) => (
          <Notification notification={item} key={n} />
        ))}
      </Styled.List>
      {hasMore && (
        <Styled.LoaderContainer ref={loaderRef}>
          <Loader />
        </Styled.LoaderContainer>
      )}
      {!hasMore && items.length === 0 && <Styled.EmptyMessage>Уведомлений пока нет :(</Styled.EmptyMessage>}
    </>
  )
}

export default NotificationsInfiniteScroll
