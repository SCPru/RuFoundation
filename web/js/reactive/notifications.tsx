import * as React from 'react';
import { useState, useRef, useEffect } from 'react';
import useConstCallback from '../util/const-callback';
import styled, { createGlobalStyle } from 'styled-components';
import NotificationsInfinityScroll from '../entrypoints/notifications-infinity-scroll';
import { Redirect } from 'react-router-dom';


interface Props {
    isAuthenticated: boolean
}

const RootStyles = createGlobalStyle`
    html {
        overflow-y: scroll;
        /*@media (prefers-color-scheme: dark) {
            filter: invert(1);
        }*/
    }
`;


const Container = styled.div`
    max-width: 600px;
    margin: 20px auto;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    background-color: #fff;
    /*@media (prefers-color-scheme: dark) {
        box-shadow: 0px 4px 20px 10px rgba(0, 0, 0, 0.1);
    }*/
    @media screen and (max-height: 740px) {
        box-shadow: none;
        margin 0;
    }
}
`;


const Title = styled.h2`
    text-align: center;
    margin-bottom: 15px;
    color: #333;
`;


const List = styled.ul`
    list-style: none;
    padding: 0;
`;


const FilterContainer = styled.div`
    display: flex;
    justify-content: center;
    margin-bottom: 25px;
`;

const RadioLabel = styled.label<{ checked: boolean }>`
    margin: 0 10px;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 20px;
    cursor: pointer;
    font-size: 14px;
    background-color: ${(props) => (props.checked ? '#f0f0f0' : 'white')};
    color: ${(props) => (props.checked ? '#000' : '#333')};
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    font-weight: ${(props) => (props.checked ? 'bold' : 'normal')};
    &:hover {
        background-color: #f8f8f8;
        border-color: #ccc;
    }
`;

const RadioInput = styled.input`
    display: none;
`;

const Notifications: React.FC<Props> = ({ isAuthenticated }) => {
    const [showUnread, setShowUnread] = useState(true);
    const reloadRef = useRef<(showUnread: boolean) => void>();

    const setReload = useConstCallback((reload: () => {}) => {
        reloadRef.current = reload;
    });

    const onFilter = useConstCallback((showUnread) => {
        setShowUnread(showUnread);
        if (reloadRef.current)
            reloadRef.current(showUnread);
    });

    if (!isAuthenticated) {
        location.href = '/-/login?to=/-/notifications';
        return <div></div>;
    }

    return (
        <Container>
            <RootStyles/>
            <Title>Уведомления</Title>
            <FilterContainer>
                <RadioLabel checked={showUnread}>
                <RadioInput
                    type='radio'
                    name='filter'
                    checked={showUnread}
                    onChange={() => onFilter(true)}
                />
                Непрочитанные
                </RadioLabel>
                <RadioLabel checked={!showUnread}>
                <RadioInput
                    type='radio'
                    name='filter'
                    checked={!showUnread}
                    onChange={() => onFilter(false)}
                />
                Все
                </RadioLabel>
                
            </FilterContainer>
            <List>
                <NotificationsInfinityScroll batchSize={10} setReload={setReload} />
            </List>
        </Container>
    );
}


export default Notifications