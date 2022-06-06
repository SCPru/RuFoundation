import * as React from 'react';
import * as ReactDOM from 'react-dom';
import {Component} from 'react';
import styled from 'styled-components';
import { v4 as uuid4 } from 'uuid';


interface Button {
    title: string
    onClick: () => void
    type?: 'primary' | 'danger' | 'default'
}


interface Props {
    isLoading?: boolean
    buttons?: Array<Button>
}

interface State {
    modalId?: string
}


class WikidotModal extends Component<Props, State> {
    state = {
        modalId: null
    };

    componentDidMount() {
        const modalId = uuid4();
        this.setState({modalId});
        addModalContainer(modalId);
    }

    componentWillUnmount() {
        removeModalContainer(this.state.modalId);
    }

    // returning a portal without explicit "any" type results in compatibility issues with older stuff
    render(): any {
        const container = getModalContainer(this.state.modalId);
        if (container)
            return ReactDOM.createPortal(<WikidotModalWindow {...this.props}/>, container);
        return null;
    }
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
  background-image: url(/static/images/progressbar.gif);
}
`;


class WikidotModalWindow extends Component<Props> {
    handleCallback(e, callback) {
        e.preventDefault();
        e.stopPropagation();
        callback();
    }

    render() {
        const { children, isLoading, buttons } = this.props;
        return (
            <Styles>
                <div className="odialog-container">
                    <div className={`owindow ${isLoading?'owait':''}`}>
                        <div className="content modal-body">
                            { children }
                            { buttons && (
                                <>
                                    <hr className="buttons-hr"/>
                                    <div className="w-modal-buttons">
                                        { buttons.map((button, i) =>
                                            <button key={i} className={`btn btn-${button.type || 'default'}`} onClick={(e) => this.handleCallback(e, button.onClick)}>
                                                {button.title}
                                            </button>
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
        <WikidotModal buttons={[{title: 'Закрыть', onClick: onCloseError}]}>
            <strong>Ошибка:</strong> {error}
        </WikidotModal>;

    uuid = addUnmanagedModal(modal);
}


export default WikidotModal