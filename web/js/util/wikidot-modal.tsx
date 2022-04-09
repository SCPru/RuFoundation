import * as React from 'react';
import { Component } from 'react';
import styled from 'styled-components';


interface Button {
    title: string
    onClick: () => void
    type?: 'primary' | 'danger' | 'default'
}


interface Props {
    isLoading?: boolean
    buttons?: Array<Button>
}


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


class WikidotModal extends Component<Props> {
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


export default WikidotModal