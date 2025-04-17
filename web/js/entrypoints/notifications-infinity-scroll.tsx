import * as React from 'react';
import { useState, useEffect } from 'react';
import InfiniteScroll from 'react-infinite-scroller';
import useConstCallback from '../util/const-callback';
import styled from 'styled-components';
import { getNotifications, Notification } from '../api/notifications';
import Loader from '../util/loader';


interface Props {
    batchSize: number
    setReload?: CallableFunction
}


const Styles = styled.div`
.loader {
    display: block;
    margin: auto;
}
.empty-message {
    text-align: center;
}
`;


const NotificationsInfinityScroll: React.FC<Props> = ({ batchSize, setReload }) => {
    const [items, setItems] = useState<Notification[]>([]);
    const [cursor, setCursor] = useState(-1); 
    const [hasMore, setHasMore] = useState(true);
    const [isFetching, setIsFetching] = useState(false);
    const [showUnread, setShowUnread] = useState(true);

    useEffect(() => {
        if (setReload)
            setReload(reload);
    }, []);

    const loadMore = useConstCallback(() => {
        if (isFetching) return;

        setIsFetching(true);

        getNotifications(cursor, batchSize, showUnread, true)
        .then((resp) => {
            setItems([...items, ...resp.notifications]);
            setCursor(resp.cursor);

            if (resp.cursor === -1)
                setHasMore(false);
        })
        .finally(() => {
            setIsFetching(false);
        });
    });

    const reload = useConstCallback((showUnread) => {
        setShowUnread(showUnread);
        setIsFetching(false);
        setItems([]);
        setCursor(-1);
        setHasMore(true);
    });

    const loader = <Loader key={0} className='loader' />

    return (
        <Styles>
            <InfiniteScroll
                loadMore={loadMore}
                hasMore={hasMore}
                loader={loader}
                initialLoad={true}
            >
                <div className='list'>
                    { items.map((item, n) => (
                        <div key={n}>
                            <div dangerouslySetInnerHTML={{ __html: item.title }}></div>
                            <div dangerouslySetInnerHTML={{ __html: item.message }}></div>
                            <hr/>
                        </div>
                    ))}
                </div>
            </InfiniteScroll>
            { !hasMore && items.length === 0 && (
                <p className='empty-message'>Уведомлений пока нет :(</p>
            )}
        </Styles>
    )
}


export default NotificationsInfinityScroll