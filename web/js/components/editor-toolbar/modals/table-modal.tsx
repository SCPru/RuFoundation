import React from "react";
import { useState } from "react";
import styled from "styled-components";
import EditorModal from "~components/editor-toolbar/modals/base-modal";
import { EditorModalStyleBase } from "~components/editor-toolbar/modals/base-modal";
import type { EditorModalComponent } from "~components/editor-toolbar/modals/base-modal";
import { MOBILE_SIZE } from "~reactive/theme/Theme.consts";


const TableModalStyle = styled(EditorModalStyleBase)`
  .editor-modal-margin input {
    max-width: 8ch;
  }

  .editor-modal-margin .editor-modal-subgrid-row {
    justify-items: left;
  }

  @media (max-width: ${MOBILE_SIZE}px) {
    .editor-modal-margin input {
      max-width: revert;
      width: 100%;
    }
  }
`;


const MIN_ROWS = 2;
const MIN_COLUMNS = 2;
const MAX_ROWS = 99;
const MAX_COLUMNS = 99;


// TODO: create separate file for some of the math functions and remove functions scattered across this whole repo
//  a job for the future me or someone else lol
// - web/js/util/tooltip.tsx @ 9:1
// - web/js/util/user-popover.ts @ 27:1
// - web/js/forum/thread-pagination.tsx @ 56:1
function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}


const TableModal: EditorModalComponent = ({
  onCancel,
  onSubmit,
}) => {
  const [rows, setRows] = useState<number>(2);
  const [columns, setColumns] = useState<number>(2);
  const [withHeader, setWithHeader] = useState<boolean>(false);
  
  const createTableRow = (length: number, isHeader: boolean = false): string => {
    const rowArray: string[] = [];
    for (let i = 0; i < length; i++) rowArray.push(`||${isHeader ? "~" : ""} Ячейка `);
    return rowArray.join("") + "||";
  };
  
  const createTable = (): string => {
    const totalRows = Number.isNaN(rows) ? MIN_ROWS : clamp(rows, MIN_ROWS, MAX_ROWS);
    const totalColumns = Number.isNaN(columns) ? MIN_COLUMNS : clamp(columns, MIN_COLUMNS, MAX_COLUMNS);
    
    const tableRows: string[] = [];
    for (let i = 0; i < totalRows; i++) tableRows.push(createTableRow(totalColumns));
    if (withHeader) tableRows[0] = createTableRow(totalColumns, true);
    return tableRows.join("\n");
  };
  
  return (
    <EditorModal onSubmit={() => onSubmit(createTable())} onCancel={() => onCancel()}>
      <TableModalStyle>
        <p className="editor-modal-header">Мастер вставки таблиц</p>
        
        <div className="editor-modal-form-grid editor-modal-margin">
          <label className="editor-modal-subgrid-row">
            Количество строк:
            <input
              type="number"
              name="wd-ed-tablewizard-rows"
              value={rows}
              min={MIN_ROWS}
              max={MAX_ROWS}
              onChange={ev => setRows(ev.target.valueAsNumber)}
              onBlur={() => {
                setRows(Number.isNaN(rows) ? MIN_ROWS : clamp(rows, MIN_ROWS, MAX_ROWS));
              }}
              placeholder={`${MIN_ROWS}`}
            />
          </label>
          <label className="editor-modal-subgrid-row">
            Количество столбцов:
            <input
              type="number"
              name="wd-ed-tablewizard-columns"
              value={columns}
              min={MIN_COLUMNS}
              max={MAX_COLUMNS}
              onChange={ev => setColumns(ev.target.valueAsNumber)}
              onBlur={() => {
                setColumns(Number.isNaN(columns) ? MIN_COLUMNS : clamp(columns, MIN_COLUMNS, MAX_COLUMNS));
              }}
              placeholder={`${MIN_COLUMNS}`}
            />
          </label>
          <label className="editor-modal-subgrid-row">
            Первая строка как заголовок:
            <input
              type="checkbox"
              checked={withHeader}
              onChange={e => setWithHeader(e.target.checked)}
            />
          </label>
        </div>
        
        <div className="editor-modal-hint">
          <b>Подсказка</b>: чтобы выровнять содержимое ячейки, добавьте сразу после
          маркера <code>||</code> символ <code>&lt;</code>, <code>=</code> или <code>&gt;</code> (для выравнивания по
          левому краю, центру и правому краю соответственно).
        </div>
      </TableModalStyle>
    </EditorModal>
  );
};


export default TableModal;
