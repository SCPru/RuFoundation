import React from "react";
import { useEffect } from "react";
import styled from "styled-components";
import WikidotModal from "~util/wikidot-modal";
import { MOBILE_SIZE } from "~reactive/theme/Theme.consts";


interface EditorModalProps {
  onSubmit: () => void,
  onCancel: () => void,
  children: React.ReactNode,
}


interface EditorModalComponentProps {
  onSubmit: (result: string) => void,
  onCancel: () => void,
  pageId?: string,
}


type EditorModalComponent = React.FC<EditorModalComponentProps>;


const EditorModalStyleBase = styled.div`
  --editor-modal-gap: 0.4em;

  * {
    box-sizing: border-box;
  }
  
  :is(button, input) {
    padding-block: 0.1em;
  }

  :is(input[type="text"], input[type="number"], textarea, select) {
    border: 1px solid #777;
    margin: 0 1px;
    padding: 1px 2px;
    background-color: #FFF;
    color: #333;
    height: 1.4lh;
  }

  button {
    padding-inline: 1em;
  }
  
  button:disabled {
    filter: contrast(0.7);
    cursor: not-allowed;
  }

  fieldset {
    display: grid;
    gap: var(--editor-modal-gap);
    border: 1px solid #aaa;
    margin: 1em auto;
    width: fit-content;
  }
  
  :is(fieldset, .editor-modal-choice-list) label {
    display: flex;
    align-items: center;
    column-gap: var(--editor-modal-gap);
  }

  textarea {
    field-sizing: content;
    width: 100%;
    min-height: 1lh;
    resize: none;
  }

  :is(fieldset, label) input[type="radio"] {
    margin-block: 0;
    margin-left: 0;
  }

  .editor-modal-header {
    text-align: center;
    font-weight: bold;
    font-size: large;
  }
  
  .editor-modal-loader-container {
    display: grid;
    place-items: center;
    margin-inline: auto;
    padding: 1em;
    background-color: rgba(119 119 119 / 0.5);
  }
  
  .editor-modal-form-grid {
    display: grid;
    grid-template-columns: max-content 1fr;
    gap: 0.1em var(--editor-modal-gap);
    width: fit-content;
    margin-inline: auto;
  }

  @media (max-width: ${MOBILE_SIZE}px) {
    .editor-modal-form-grid {
      grid-template-columns: 1fr;
    }
  }

  .editor-modal-subgrid-row {
    display: grid;
    grid-column: -1 / 1;
    grid-template-columns: subgrid;
    row-gap: 0.1em;
    align-items: center;
  }

  .editor-modal-scroll-area {
    max-height: 128px;
    overflow-y: auto;
    scrollbar-gutter: stable;
  }
  
  .editor-modal-margin {
    margin-block: 1em;
  }
  
  .editor-modal-hint {
    text-align: center;
    text-wrap: balance;
  }
`;


const EditorModal: React.FC<EditorModalProps> = (
  {
    onSubmit,
    onCancel,
    children,
  },
) => {
  useEffect(() => {
    const keyPressHandler = (ev: KeyboardEvent) => {
      if (ev.code === "Escape") onCancel();
    };
    document.addEventListener("keydown", keyPressHandler);
    return () => document.removeEventListener("keydown", keyPressHandler);
  }, [onCancel]);
  
  return (
    <WikidotModal buttons={[
      {
        title: "Отменить",
        onClick: onCancel,
      },
      {
        title: "Вставить код",
        onClick: onSubmit,
      },
    ]}>
      {children}
    </WikidotModal>
  );
};


export default EditorModal;
export { EditorModalStyleBase };
export type { EditorModalComponentProps, EditorModalComponent };
