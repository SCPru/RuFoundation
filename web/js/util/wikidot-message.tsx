import * as React from 'react';
import * as ReactDOM from 'react-dom';
import {Component} from 'react';
import styled from 'styled-components';


interface Button {
    title: string
    onClick: () => void
}


interface Props {
    buttons?: Array<Button>
}

const Styles = styled.div`
.w-message{
    position: absolute;
    right: 2em;
    border: 1px dashed #888;
    padding: 0.5em 1em;
    background-color: #FDD;
    max-width: 20em;
    opacity: 0.9;
    z-index: 1;
}
`;

class WikidotMessage extends Component<Props> {

    handleCallback(e, callback) {
        e.preventDefault();
        e.stopPropagation();
        callback();
    }

    render() {
        const { children, buttons } = this.props;
        return (
            <Styles>
                <div className="w-message">
                    { children }
                    <br/>
                    { buttons.map((button, i) =>
                            <a key={i} onClick={(e) => this.handleCallback(e, button.onClick)}>
                                {button.title}
                            </a>
                    ).reduce((prev, curr) => [prev, " | ", curr]) }
                </div>
            </Styles>
        )
    }
}

function getMessageContainer() {
    return document.getElementById('action-area-top');
}


function addMessage(message: JSX.Element) {
    ReactDOM.render(message, getMessageContainer());
}


function removeMessage() {
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
    
    const message = <WikidotMessage buttons={[{title: 'Вниз к редактору', onClick: onDown}, {title: 'Закрыть блок', onClick: onClose}]}>
        Подсказка: это лишь предварительный просмотр.
        <br/>
        Если закрыть эту страницу сейчас, изменения не сохранятся.
    </WikidotMessage>;

    addMessage(message);
    setTimeout(() => {
        window.scrollTo(window.scrollX, document.body.scrollTop);
    }, 1);
}



export default WikidotMessage
