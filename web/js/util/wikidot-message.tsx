import * as React from 'react';
import * as ReactDOM from 'react-dom';
import useConstCallback from './const-callback';
import styled from 'styled-components';
import formatDate from "./date-format";
import { UserData } from "../api/user";
import UserView from "./user-view";


interface Button {
    title: string
    onClick: () => void
}


interface Props {
    buttons?: Array<Button>
    background?: string
}

const Styles = styled.div`
.w-message{
    position: absolute;
    right: 2em;
    border: 1px dashed #888;
    padding: 0.5em 1em;
    max-width: 20em;
    opacity: 0.9;
    z-index: 999999;
}
`;

const WikidotMessage:React.FC<Props> = ({ children, buttons, background }: Props) => {

    const handleCallback = useConstCallback((e, callback) => {
        e.preventDefault();
        e.stopPropagation();
        callback();
    });

    return (
        <Styles>
            <div className="w-message" style={{ background: background }}>
                { children }
                <br/>
                { buttons.map((button, i) =>
                    <React.Fragment key={i}>
                        <a onClick={(e) => handleCallback(e, button.onClick)}>
                            {button.title}
                        </a>
                        {(i !== buttons.length-1) && ' | '}
                    </React.Fragment>
                ) }
            </div>
        </Styles>
    )
}

function getMessageContainer() {
    return document.getElementById('action-area-top');
}


function addMessage(message: JSX.Element) {
    ReactDOM.render(message, getMessageContainer());
}


export function removeMessage() {
    const node = getMessageContainer();
    ReactDOM.unmountComponentAtNode(node);
}


export function showPreviewMessage() {
    const onDown = () => {
        setTimeout(() => {
            window.scrollTo(window.scrollX, document.body.scrollHeight);
        }, 1);
    }
    
    const onClose = () => {
        removeMessage();
    }
    
    const message = <WikidotMessage background={"#FDD"} buttons={[{title: 'Вниз к редактору', onClick: onDown}, {title: 'Закрыть блок', onClick: onClose}]}>
        Подсказка: это лишь предварительный просмотр.
        <br/>
        Если закрыть эту страницу сейчас, изменения не сохранятся.
    </WikidotMessage>;

    addMessage(message);
    setTimeout(() => {
        window.scrollTo(window.scrollX, document.body.scrollTop);
    }, 1);
}


export function showVersionMessage(num: number, date: Date, user: UserData, pageId: string) {
    const onDown = () => {
        setTimeout(() => {
            window.scrollTo(window.scrollX, document.body.scrollHeight);
        }, 1);
    }

    const onClose = () => {
        removeMessage();
    }

    const message = <WikidotMessage background={"#EEF"} buttons={[{title: 'Вниз к версиям', onClick: onDown}, {title: 'Закрыть блок', onClick: onClose}]}>
        <table>
            <tbody>
            <tr>
                <td>
                    Правка №:
                </td>
                <td>
                    {num}
                </td>
            </tr>
            <tr>
                <td>Дата создания:</td>
                <td>
                    {formatDate(date)}
                </td>
            </tr>
            <tr>
                <td>От:</td>
                <td>
                    <UserView data={user} />
                </td>
            </tr>
            <tr>
                <td>
                    Имя страницы:
                </td>
                <td>
                    {pageId}
                </td>
            </tr>
            </tbody>
        </table>
    </WikidotMessage>;

    addMessage(message);
    setTimeout(() => {
        window.scrollTo(window.scrollX, document.body.scrollTop);
    }, 1);
}



export default WikidotMessage
