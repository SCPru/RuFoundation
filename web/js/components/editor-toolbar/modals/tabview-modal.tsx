import React from "react";
import { useCallback, useState } from "react";
import styled from "styled-components";
import EditorModal from "~components/editor-toolbar/modals/base-modal";
import { EditorModalStyleBase } from "~components/editor-toolbar/modals/base-modal";
import type { EditorModalComponent } from "~components/editor-toolbar/modals/base-modal";
import { v4 as uuid4 } from "uuid";


interface TabviewEntry {
  title: string;
  id: string;
}


const TabviewModalStyle = styled(EditorModalStyleBase)`
  .tabview-modal-add-new-entry {
    display: flex;
    align-items: baseline;
    column-gap: var(--editor-modal-gap);
  }

  .tabview-modal-entry-container {
    height: 128px;
  }

  .tabview-modal-entry-container-grid {
    display: grid;
    grid-template-columns: 4ch auto min-content;
    row-gap: 0.1em;
  }

  .tabview-modal-entry-container-grid-row {
    align-items: baseline;
    justify-items: end;
    column-gap: 1em;
    text-align: center;
  }
  
  #wd-ed-tabviewwizard-input {
    flex-grow: 1;
  }
`;


const TabviewModal: EditorModalComponent = ({
  onCancel,
  onSubmit,
}) => {
  const [entryArray, setEntryArray] = useState<TabviewEntry[]>([]);
  const [titleInput, setTitleInput] = useState<string>("");
  
  const addTitleEntry = useCallback(() => {
    const input = titleInput.trim();
    if (!input) return;
    setEntryArray(prevState => [...prevState, {
      title: input,
      id: uuid4(),
    }]);
    setTitleInput("");
  }, [titleInput]);
  
  const removeTitleEntry = useCallback((entryId: string) => {
    setEntryArray(prevState => prevState.filter(entry => entry.id !== entryId));
  }, []);
  
  const createTabview = useCallback((): string => {
    if (!entryArray.length) return "";
    const tabs = entryArray.map(entry => `[[tab ${entry.title}]]\n\n[[/tab]]`);
    return "[[tabview]]\n" + tabs.join("\n") + "\n[[/tabview]]";
  }, [entryArray]);
  
  return (
    <EditorModal onSubmit={() => onSubmit(createTabview())} onCancel={() => onCancel()}>
      <TabviewModalStyle>
        <p className="editor-modal-header">Мастер вставки вкладок</p>
        <div className="tabview-modal-add-new-entry">
          <label htmlFor="wd-ed-tabviewwizard-input">Заголовок:</label>
          <input
            id="wd-ed-tabviewwizard-input"
            type="text"
            value={titleInput}
            onChange={ev => setTitleInput(ev.target.value)}
            onKeyDown={ev => {
              if (ev.code === "Enter") addTitleEntry();
            }}
          />
          <button
            type="button"
            onClick={addTitleEntry}
          >Добавить
          </button>
        </div>
        <hr className="buttons-hr"/>
        <div className="tabview-modal-entry-container editor-modal-scroll-area">
          <div className="tabview-modal-entry-container-grid" role="list">
            {entryArray.map((item, idx) => (
              <div
                className="tabview-modal-entry-container-grid-row editor-modal-subgrid-row"
                role="listitem"
                key={item.id}>
                <span>{`${idx + 1}.`}</span>
                <span>{item.title}</span>
                <button
                  type="button"
                  onClick={() => removeTitleEntry(item.id)}
                  aria-label={`Удалить вкладку «${item.title}»`}
                >×
                </button>
              </div>
            ))}
          </div>
        </div>
      </TabviewModalStyle>
    </EditorModal>
  );
};


export default TabviewModal;
