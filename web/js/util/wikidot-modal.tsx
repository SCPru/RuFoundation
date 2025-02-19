import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { useState, useEffect } from 'react';
import useConstCallback from './const-callback';
import styled from 'styled-components';
import { v4 as uuid4 } from 'uuid';
import { ArticleLogEntry, revertArticleRevision } from "../api/articles";


interface Button {
    title: string
    onClick: () => void
    type?: 'primary' | 'danger' | 'default'
}


interface Props {
    isLoading?: boolean
    isError?: boolean
    buttons?: Array<Button>
}


const WikidotModal: React.FC<Props> = ({ children, isLoading, isError, buttons }) => {
    const [modalId, setModalId] = useState('');

    useEffect(() => {
        const newModalId = uuid4();
        setModalId(newModalId);
        addModalContainer(newModalId);

        return () => {
            removeModalContainer(newModalId);
        }
    }, []);

    // returning a portal without explicit "any" type results in compatibility issues with older stuff
    
    const container = getModalContainer(modalId);
    if (container)
        return ReactDOM.createPortal(<WikidotModalWindow children={children} isLoading={isLoading} isError={isError} buttons={buttons} id={modalId} />, container);
    return null;
}


//
const Styles = styled.div`
.odialog-container {
  position: fixed;
  z-index: 9999;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0000007f;
}
.owindow {
  max-width: 50em;
  width: auto;
}
.buttons-hr {
  margin-left: 0;
  margin-right: 0;
}
.w-modal-buttons {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
}
.owindow.owait .content {
  background-image: url(/-/static/images/progressbar.gif);
}
`;


const WikidotModalWindow: React.FC<Props & {id: string}> = ({ children, isLoading, isError, buttons, id }) => {
    const handleCallback = useConstCallback((e, callback) => {
        e.preventDefault();
        e.stopPropagation();
        callback();
    });

    return (
        <Styles>
            <div className="odialog-container">
                <div id={`owindow-${id}`} className={`owindow ${isLoading?'owait':''} ${isError?'error':''}`}>
                    <div className="content modal-body">
                        { children }
                        { buttons && (
                            <>
                                <hr className="buttons-hr"/>
                                <div className="w-modal-buttons button-bar modal-footer">
                                    { buttons.map((button, i) =>
                                        <a key={i} className={`btn btn-${button.type || 'default'} button button-close-message`} onClick={(e) => handleCallback(e, button.onClick)}>
                                            {button.title}
                                        </a>
                                    ) }
                                </div>
                            </>
                        ) }
                    </div>
                </div>
            </div>
        </Styles>
    )
}


function getModalContainerElement() {
    return document.getElementById('w-modals');
}

function addModalContainer(id) {
    const node = document.createElement('div');
    node.setAttribute('id', `modal-${id}`);
    getModalContainerElement()?.appendChild(node);
    return node;
}

function getModalContainer(id) {
    return getModalContainerElement()?.querySelector(`#modal-${id}`);
}

function removeModalContainer(id) {
    const node = getModalContainer(id);
    node?.parentNode.removeChild(node);
}

export function addUnmanagedModal(modal) {
    const id = uuid4();
    const container = addModalContainer(id);
    ReactDOM.render(modal, container);
    return id;
}

export function updateUnmanagedModal(id, modal) {
    const container = getModalContainer(id);
    if (container) {
        ReactDOM.render(modal, container);
    }
}

export function removeUnmanagedModal(id) {
    const container = getModalContainer(id);
    if (container) {
        ReactDOM.unmountComponentAtNode(container);
    }
    removeModalContainer(id);
}


export function showErrorModal(error) {
    let uuid: string | null = null;

    const onCloseError = () => {
        removeUnmanagedModal(uuid);
    };

    const modal =
        <WikidotModal buttons={[{title: 'Закрыть', onClick: onCloseError}]} isError>
            <p><strong>Ошибка:</strong> {error}</p>
        </WikidotModal>;

    uuid = addUnmanagedModal(modal);
}


export function showRevertModal(pageId: string, entry: ArticleLogEntry) {
    let uuid: string | null = null;

    const onClose = () => {
        removeUnmanagedModal(uuid);
    };

    const onRevert = () => {
        onClose();
        revertArticleRevision(pageId, entry.revNumber).then(function (pageData) {
            window.location.href = `/${pageData.pageId}`;
        }).catch(error => {showErrorModal(error.toString())});
    }

    const modal =
        <WikidotModal buttons={[{title: 'Отменить', onClick: onClose}, {title: "Да, вернуть", onClick: onRevert}]}>
            <h1>Вернуть версию страницы?</h1>
            <p>Вы уверены, что хотите откатить версию страницы к ревизии <strong>№{entry.revNumber}</strong>?</p>
        </WikidotModal>;

    uuid = addUnmanagedModal(modal);
}


export default WikidotModal