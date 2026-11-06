import React from "react";
import { useEffect, useLayoutEffect, useRef, useCallback, useMemo, useState } from "react";
import styled from "styled-components";
import { css } from "styled-components";
import type { EditorModalComponent } from "~components/editor-toolbar/modals/base-modal";
import TableModal from "~components/editor-toolbar/modals/table-modal";
import TabviewModal from "~components/editor-toolbar/modals/tabview-modal";
import LinkModal from "~components/editor-toolbar/modals/link-modal";
import ImageModal from "~components/editor-toolbar/modals/image-modal";


interface TextSelection {
  start: number,
  end: number,
}


interface EditHistoryEntry {
  source: string,
  selection: TextSelection,
}


interface EditHistory {
  entries: EditHistoryEntry[],
  pointer: number,
  lastEdit: number,
  lastEditBatch: number,
}


type FKey = `F${1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12}`;
type Special = "Tab" | "Escape" | FKey;
type Letter =
  | "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" | "J" | "K" | "L" | "M"
  | "N" | "O" | "P" | "Q" | "R" | "S" | "T" | "U" | "V" | "W" | "X" | "Y" | "Z";
type Digit =
  | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | "0";

type Modifiers = `${"Ctrl+" | ""}${"Alt+" | ""}${"Shift+" | ""}`;
type ModifierPrefix = Exclude<Modifiers, "">;

type KeybindLiteral =
  | `${ModifierPrefix}${Letter | Digit}`
  | `${Modifiers}${Special}`;


interface EditorToolbarButtonProps {
  onClick: () => void,
  title: string,
  className?: string,
  keybind?: KeybindLiteral,
  disabled?: boolean,
}


interface EditorToolbarPanelProps {
  readonly textareaRef: React.RefObject<HTMLTextAreaElement>,
  onSourceChange: (text: string) => void,
  className?: string,
  pageId?: string,
  disabled?: boolean,
}


const isAppleDevice = /Mac|iPhone|iPad/.test(navigator.userAgent);
const ctrlRepr = isAppleDevice ? "⌘" : "Ctrl";


function keyCodeToLetter(keycode: string): string | null {
  const specialKeyRegex = /^(?:Tab|Escape|F(?:[1-9]|1[0-2]))$/;
  if (specialKeyRegex.test(keycode)) return keycode;
  
  const letterRegex = /(?:Key|Digit)(?<char>[A-Z0-9])/;
  const key = keycode.match(letterRegex)?.groups?.char;
  return key ? key : null;
}


function eventToLiteral(ev: KeyboardEvent): KeybindLiteral | null {
  const key = keyCodeToLetter(ev.code);
  if (!key) return null;
  
  const ctrl = isAppleDevice ? ev.metaKey : ev.ctrlKey;
  // TIL apparently Apple devices have both ctrl and meta buttons
  const nonNative = isAppleDevice ? ev.ctrlKey : ev.metaKey;
  if (nonNative) return null;
  
  const prefix = `${ctrl ? "Ctrl+" : ""}${ev.altKey ? "Alt+" : ""}${ev.shiftKey ? "Shift+" : ""}`;
  if (!prefix && key.length === 1) return null;
  
  return `${prefix}${key}` as KeybindLiteral;
}


type ModalName = "table" | "tabview" | "link" | "image";


interface EditorModalState {
  name: ModalName,
  selection: TextSelection,
}


const EDIT0R_MODALS: Record<ModalName, EditorModalComponent> = {
  table: TableModal,
  tabview: TabviewModal,
  link: LinkModal,
  image: ImageModal,
};


const EditorToolbarButton: React.FC<EditorToolbarButtonProps> = ({
  onClick,
  title,
  className,
  keybind,
  disabled,
}) => {
  return (
    <button
      type="button"
      className={className}
      onClick={onClick}
      title={keybind ? `${title} (${keybind.replace("Ctrl", ctrlRepr)})` : title}
      aria-keyshortcuts={keybind ? `${keybind.replace("Ctrl", isAppleDevice ? "Meta" : "Control")}` : undefined}
      disabled={disabled}
    />
  );
};


interface EditorButtonMethods {
  insertInline: (before: string, after?: string, togglable?: boolean) => void,
  insertBlock: (before: string, after: string, message?: string) => void,
  insertList: (marker: string, message?: string) => void,
  insertPlain: (before: string, after?: string, template?: string) => void,
  indent: (isIncrement: boolean) => void,
  modalOpen: (modalName: ModalName) => void,
}


type EditorCallback = (editor: EditorButtonMethods) => void;


interface ButtonData {
  className: string,
  title: string,
  onClick: EditorCallback,
  keybind?: KeybindLiteral,
  iconPath?: string,
}


interface ToolbarGroup {
  className: string,
  entry: ButtonData[],
}


const textFormatButtonData: ButtonData[] = [
  {
    className: "weditor-bold",
    title: "Полужирный",
    onClick: editor => editor.insertInline("**"),
    keybind: "Ctrl+B",
    iconPath: "/-/static/images/editor/mitten-icons/bold.svg",
  },
  {
    className: "weditor-italic",
    title: "Курсивный",
    onClick: editor => editor.insertInline("//"),
    keybind: "Ctrl+I",
    iconPath: "/-/static/images/editor/mitten-icons/italic.svg",
  },
  {
    className: "weditor-underline",
    title: "Подчёркнутый",
    onClick: editor => editor.insertInline("__"),
    keybind: "Ctrl+U",
    iconPath: "/-/static/images/editor/mitten-icons/underline.svg",
  },
  {
    className: "weditor-strikethrough",
    title: "Перечёркнутый",
    onClick: editor => editor.insertInline("--"),
    iconPath: "/-/static/images/editor/mitten-icons/strikethrough.svg",
  },
  {
    className: "weditor-teletype",
    title: "Моноширинный",
    onClick: editor => editor.insertInline("{{", "}}"),
    iconPath: "/-/static/images/editor/mitten-icons/monospace.svg",
  },
  {
    className: "weditor-superscript",
    title: "Верхний регистр",
    onClick: editor => editor.insertInline("^^"),
    iconPath: "/-/static/images/editor/mitten-icons/upper.svg",
  },
  {
    className: "weditor-subscript",
    title: "Нижний регистр",
    onClick: editor => editor.insertInline(",,"),
    iconPath: "/-/static/images/editor/mitten-icons/lower.svg",
  },
  {
    className: "weditor-raw",
    title: "Сырой текст",
    onClick: editor => editor.insertInline("@@"),
    iconPath: "/-/static/images/editor/mitten-icons/raw.svg",
  },
  {
    className: "weditor-textcolor",
    title: "Цветной текст",
    onClick: editor => editor.insertInline("##цвет|", "##", false),
    iconPath: "/-/static/images/editor/mitten-icons/text-color.svg",
  },
];

const paragraphFormatButtonData: ButtonData[] = [
  {
    className: "weditor-alignleft",
    title: "Выравнивание по левому краю",
    onClick: editor => editor.insertBlock("[[<]]", "[[/<]]"),
    keybind: "Ctrl+L",
    iconPath: "/-/static/images/editor/mitten-icons/align-left.svg",
  },
  {
    className: "weditor-alignmiddle",
    title: "Выравнивание по центру",
    onClick: editor => editor.insertBlock("[[=]]", "[[/=]]"),
    keybind: "Ctrl+E",
    iconPath: "/-/static/images/editor/mitten-icons/align-center.svg",
  },
  {
    className: "weditor-alignright",
    title: "Выравнивание по правому краю",
    onClick: editor => editor.insertBlock("[[>]]", "[[/>]]"),
    keybind: "Ctrl+R",
    iconPath: "/-/static/images/editor/mitten-icons/align-right.svg",
  },
  {
    className: "weditor-alignjustify",
    title: "Выравнивание по ширине",
    onClick: editor => editor.insertBlock("[[==]]", "[[/==]]"),
    keybind: "Ctrl+J",
    iconPath: "/-/static/images/editor/mitten-icons/align-justify.svg",
  },
];

const listFormatButtonData: ButtonData[] = [
  {
    className: "weditor-deflist",
    title: "Список определений",
    onClick: editor => editor.insertList(": Термин : ", "Определение"),
    iconPath: "/-/static/images/editor/mitten-icons/definition-list.svg",
  },
  {
    className: "weditor-bullist",
    title: "Маркированный список",
    onClick: editor => editor.insertList("*"),
    iconPath: "/-/static/images/editor/mitten-icons/bullet-list.svg",
  },
  {
    className: "weditor-numlist",
    title: "Нумерованный список",
    onClick: editor => editor.insertList("#"),
    iconPath: "/-/static/images/editor/mitten-icons/numberic-list.svg",
  },
  {
    className: "weditor-incindent",
    title: "Увеличить отступ",
    onClick: editor => editor.indent(true),
    keybind: "Tab",
    iconPath: "/-/static/images/editor/mitten-icons/inc-indent.svg",
  },
  {
    className: "weditor-decindent",
    title: "Уменьшить отступ",
    onClick: editor => editor.indent(false),
    keybind: "Shift+Tab",
    iconPath: "/-/static/images/editor/mitten-icons/dec-indent.svg",
  },
];

const blockFormatButtonData: ButtonData[] = [
  {
    className: "weditor-collapsible",
    title: "Раскрываемый блок",
    onClick: editor => editor.insertBlock("[[collapsible show=\"+ Надпись при открытии спойлера\" hide=\"- Надпись при закрытии спойлера\"]]", "[[/collapsible]]", "Содержимое скрываемого блока"),
    iconPath: "/-/static/images/editor/mitten-icons/collapsible.svg",
  },
  {
    className: "weditor-quote",
    title: "Блок цитирования",
    onClick: editor => editor.insertBlock("[[blockquote]]", "[[/blockquote]]", "Содержимое блока цитирования"),
    iconPath: "/-/static/images/editor/mitten-icons/quoteblock.svg",
  },
  {
    className: "weditor-div",
    title: "div-элемент",
    onClick: editor => editor.insertBlock("[[div]]", "[[/div]]", "Содержимое блока"),
    iconPath: "/-/static/images/editor/mitten-icons/div.svg",
  },
];

const inlineFormatButtonData: ButtonData[] = [
  {
    className: "weditor-footnote",
    title: "Сноска",
    onClick: editor => editor.insertInline("[[footnote]]", "[[/footnote]]", false),
    iconPath: "/-/static/images/editor/mitten-icons/footnote.svg",
  },
  {
    className: "weditor-span",
    title: "span-элемент",
    onClick: editor => editor.insertInline("[[span]]", "[[/span]]", false),
    iconPath: "/-/static/images/editor/mitten-icons/span.svg",
  },
  {
    className: "weditor-extlink",
    title: "Внешняя ссылка",
    onClick: editor => editor.insertInline("[*ссылка ", "]", false),
    iconPath: "/-/static/images/editor/mitten-icons/external-link.svg",
  },
  {
    className: "weditor-link",
    title: "Внутренняя ссылка",
    onClick: editor => editor.insertInline("[[[*статья|", "]]]", false),
    iconPath: "/-/static/images/editor/mitten-icons/internal-link.svg",
  },
  {
    className: "weditor-image",
    title: "Изображение",
    onClick: editor => editor.insertInline("[[image ", "]]", false),
    iconPath: "/-/static/images/editor/mitten-icons/image.svg",
  },
];

const miscFormatButtonData: ButtonData[] = [
  {
    className: "weditor-hr",
    title: "Горизонтальная линия",
    onClick: editor => editor.insertPlain("----"),
    iconPath: "/-/static/images/editor/mitten-icons/hr.svg",
  },
  {
    className: "weditor-clearfloat",
    title: "Сброс плавающих элементов",
    onClick: editor => editor.insertPlain("~~~~"),
    iconPath: "/-/static/images/editor/mitten-icons/float-clear.svg",
  },
  {
    className: "weditor-lines",
    title: "Вставка пустых строк",
    onClick: editor => editor.insertPlain("[[lines ", "]]", "число"),
    iconPath: "/-/static/images/editor/mitten-icons/lines.svg",
  },
];

const wizardButtonData: ButtonData[] = [
  {
    className: "weditor-tablewiz",
    title: "Мастер вставки таблиц",
    onClick: editor => editor.modalOpen("table"),
    iconPath: "/-/static/images/editor/mitten-icons/table-wizard.svg",
  },
  {
    className: "weditor-tabviewwiz",
    title: "Мастер вставки вкладок",
    onClick: editor => editor.modalOpen("tabview"),
    iconPath: "/-/static/images/editor/mitten-icons/tabview-wizard.svg",
  },
  {
    className: "weditor-pagelinkwiz",
    title: "Мастер вставки ссылок",
    onClick: editor => editor.modalOpen("link"),
    iconPath: "/-/static/images/editor/mitten-icons/link-wizard.svg",
  },
  {
    className: "weditor-imagewiz",
    title: "Мастер вставки изображений",
    onClick: editor => editor.modalOpen("image"),
    iconPath: "/-/static/images/editor/mitten-icons/image-wizard.svg",
  },
];

const toolbarButtonGroups: ToolbarGroup[] = [
  {
    className: "text-format-options",
    entry: textFormatButtonData,
  },
  {
    className: "paragraph-format-options",
    entry: paragraphFormatButtonData,
  },
  {
    className: "list-format-options",
    entry: listFormatButtonData,
  },
  {
    className: "block-format-options",
    entry: blockFormatButtonData,
  },
  {
    className: "inline-format-options",
    entry: inlineFormatButtonData,
  },
  {
    className: "misc-format-options",
    entry: miscFormatButtonData,
  },
  {
    className: "wizard-format-options",
    entry: wizardButtonData,
  },
];


const EditorToolbarPanel__Bare: React.FC<EditorToolbarPanelProps> = ({
  textareaRef,
  onSourceChange,
  className,
  pageId,
  disabled,
}) => {
  const [keyboardTrapped, setKeyboardTrapped] = useState<boolean>(false);
  const [currentModal, setCurrentModal] = useState<EditorModalState | null>(null);
  
  const selectionRef = useRef<TextSelection | null>(null);
  const editHistoryRef = useRef<EditHistory>({
    entries: [],
    pointer: -1,
    lastEdit: 0,
    lastEditBatch: 0,
  });
  
  // Methods
  
  const addHistoryEntry = useCallback((entry: EditHistoryEntry, rewritable = false) => {
    const MAX_ENTRY_SIZE = 256;
    const MIN_DELAY_MS = 350;
    const MAX_DELAY_MS = 1000;
    
    const history = editHistoryRef.current;
    const currentTime = Date.now();
    const shouldRewrite = rewritable
      && (currentTime - history.lastEdit) < MIN_DELAY_MS
      && (currentTime - history.lastEditBatch) < MAX_DELAY_MS;
    
    history.entries.length = history.pointer + 1;
    if (shouldRewrite) {
      history.entries[history.pointer] = entry;
    } else {
      history.entries.push(entry);
      if (history.entries.length > MAX_ENTRY_SIZE) {
        history.entries.shift();
      }
      history.pointer = history.entries.length - 1;
      history.lastEditBatch = currentTime;
    }
    history.lastEdit = rewritable ? currentTime : 0;
  }, []);
  
  const renderHistoryEntry = useCallback((entry: EditHistoryEntry) => {
    selectionRef.current = entry.selection;
    onSourceChange(entry.source);
  }, [onSourceChange]);
  
  const applyChanges = useCallback((source: string, selection: TextSelection) => {
    selectionRef.current = selection;
    addHistoryEntry({
      source,
      selection,
    });
    onSourceChange(source);
  }, [addHistoryEntry, onSourceChange]);
  
  const insertInline = useCallback((before: string, after: string = before, togglable = true) => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    
    const {
      selectionStart,
      selectionEnd,
      value: taValue,
    } = textarea;
    
    const isToggling = selectionStart >= before.length
      && taValue.startsWith(before, selectionStart - before.length)
      && taValue.startsWith(after, selectionEnd)
      && togglable;
    
    const selectionShift = isToggling ? -before.length : before.length;
    
    // `textarea.value` is always `source` as long as we call `onSourceChange` in one way or another
    const selectedText = taValue.slice(selectionStart, selectionEnd);
    const selection = {
      start: selectionStart + selectionShift,
      end: selectionEnd + selectionShift,
    };
    const source = isToggling
      ? taValue.slice(0, selectionStart - before.length) + selectedText + taValue.slice(selectionEnd + after.length)
      : taValue.slice(0, selectionStart) + before + selectedText + after + taValue.slice(selectionEnd);
    
    applyChanges(source, selection);
  }, [applyChanges]);
  
  const insertBlock = useCallback((before: string, after: string, message: string = "") => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    
    const {
      selectionStart,
      selectionEnd,
      value: taValue,
    } = textarea;
    
    const newlinePrefix = taValue.startsWith("\n", selectionStart - 1) || selectionStart === 0 ? "" : "\n\n";
    const newlineSuffix = taValue.endsWith("\n", selectionEnd + 1) ? "" : "\n\n";
    
    const hasSelection = selectionStart !== selectionEnd;
    const content = hasSelection ? taValue.slice(selectionStart, selectionEnd) : message;
    
    const selection = {
      start: selectionStart + newlinePrefix.length + before.length + 1,
      end: selectionStart + newlinePrefix.length + before.length + 1 + content.length,
    };
    const injectable = newlinePrefix + before + "\n" + content + "\n" + after + newlineSuffix;
    const source = taValue.slice(0, selectionStart) + injectable + taValue.slice(selectionEnd);
    
    applyChanges(source, selection);
  }, [applyChanges]);
  
  const insertList = useCallback((marker: string, message: string = "") => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    
    const {
      selectionStart,
      selectionEnd,
      value: taValue,
    } = textarea;
    const newlinePrefix = taValue.startsWith("\n", selectionStart - 1) || selectionStart === 0 ? "" : "\n";
    const newlineSuffix = taValue.endsWith("\n", selectionEnd + 1) ? "" : "\n";
    const markerPrefix = `${marker} `;
    
    const hasSelection = selectionStart !== selectionEnd;
    const content = hasSelection ? taValue.slice(selectionStart, selectionEnd).replaceAll("\n", "\n" + markerPrefix) : message;
    
    const selection = {
      start: selectionStart + newlinePrefix.length + markerPrefix.length,
      end: selectionStart + newlinePrefix.length + markerPrefix.length + content.length,
    };
    const injectable = newlinePrefix + markerPrefix + content + newlineSuffix;
    const source = taValue.slice(0, selectionStart) + injectable + taValue.slice(selectionEnd);
    
    applyChanges(source, selection);
  }, [applyChanges]);
  
  const indent = useCallback((isIncrement: boolean) => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    
    const whitespaceRegex = /^\s/;
    
    const {
      selectionStart,
      selectionEnd,
      value: taValue,
    } = textarea;
    
    const hasSelection = selectionStart !== selectionEnd;
    const beginningIdx = taValue.slice(0, selectionStart).lastIndexOf("\n") + 1;
    const endingIdx = taValue.indexOf("\n", hasSelection && taValue[selectionEnd - 1] === "\n" ? selectionEnd - 1 : selectionEnd);
    const selectedBlock = taValue.slice(beginningIdx, endingIdx);
    
    const lines = selectedBlock.split("\n");
    const tmpLines: string[] = [];
    for (const line of lines) tmpLines.push(isIncrement ? ` ${line}` : line.replace(whitespaceRegex, ""));
    const injectable = tmpLines.join("\n");
    
    const source = taValue.slice(0, beginningIdx) + injectable + taValue.slice(endingIdx);
    const selection = {
      start: beginningIdx,
      end: endingIdx + injectable.length - selectedBlock.length,
    };
    
    if (injectable === selectedBlock) {
      // React no-ops if source doesn't change therefore `useLayoutEffect` doesn't execute
      textarea.setSelectionRange(selection.start, selection.end);
      textarea.focus();
      return;
    }
    
    applyChanges(source, selection);
  }, [applyChanges]);
  
  const insertPlain = useCallback((before: string, after: string = "", template: string = "") => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    
    const {
      selectionStart,
      selectionEnd,
      value: taValue,
    } = textarea;
    
    const newlinePrefix = taValue.startsWith("\n", selectionStart - 1) || selectionStart === 0 ? "" : "\n";
    const newlineSuffix = taValue.endsWith("\n", selectionEnd + 1) ? "" : "\n";
    
    const injectable = newlinePrefix + before + template + after + newlineSuffix;
    const source = taValue.slice(0, selectionStart) + injectable + taValue.slice(selectionEnd);
    const selection = {
      start: selectionStart + newlinePrefix.length + before.length,
      end: selectionStart + newlinePrefix.length + before.length + template.length,
    };
    
    applyChanges(source, selection);
  }, [applyChanges]);
  
  const modalOpen = useCallback((modalName: ModalName) => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    
    const {
      selectionStart,
      selectionEnd,
    } = textarea;
    
    setCurrentModal({
      name: modalName,
      selection: {
        start: selectionStart,
        end: selectionEnd,
      },
    });
  }, [setCurrentModal]);
  
  const modalClose = useCallback(() => {
    if (currentModal) selectionRef.current = currentModal.selection;
    setCurrentModal(null);
  }, [setCurrentModal, currentModal]);
  
  const modalSubmit = useCallback((result: string) => {
    const textarea = textareaRef.current;
    if (!textarea || !currentModal) return;
    
    const {
      start,
      end,
    } = currentModal.selection;
    
    const source = textarea.value.slice(0, start) + result + textarea.value.slice(end);
    const selection = {
      start: start,
      end: start + result.length,
    };
    modalClose();
    applyChanges(source, selection);
  }, [currentModal, modalClose, applyChanges]);
  
  const modalRender = useCallback(() => {
    if (!currentModal) return;
    const EditorModal = EDIT0R_MODALS[currentModal.name];
    return <EditorModal onSubmit={modalSubmit} onCancel={modalClose} pageId={pageId} />;
  }, [currentModal, modalSubmit, modalClose]);
  
  const undo = useCallback(() => {
    const history = editHistoryRef.current;
    if (history.pointer > 0) {
      history.pointer -= 1;
      renderHistoryEntry(history.entries[history.pointer]);
    }
  }, [renderHistoryEntry]);
  
  const redo = useCallback(() => {
    const history = editHistoryRef.current;
    if (history.pointer < history.entries.length - 1) {
      history.pointer += 1;
      renderHistoryEntry(history.entries[history.pointer]);
    }
  }, [renderHistoryEntry]);
  
  // Data
  
  const editorMethods: EditorButtonMethods = {
    insertInline,
    insertBlock,
    insertList,
    insertPlain,
    indent,
    modalOpen,
  }
  
  const actions = useMemo(() => {
    const keybindActionsMap: Map<KeybindLiteral, EditorCallback> = new Map([
      ["Ctrl+Z", () => undo()],
      ["Ctrl+Shift+Z", () => redo()],
      ["Escape", () => {
        setKeyboardTrapped(false);
        textareaRef.current?.blur();
      }],
    ]);
    
    for (const buttonGroup of toolbarButtonGroups) {
      for (const button of buttonGroup.entry) {
        if (button.keybind) keybindActionsMap.set(button.keybind, button.onClick);
      }
    }
    
    return keybindActionsMap;
  }, [setKeyboardTrapped, undo, redo /* Jung Kook - Please Don't Change */]);
  
  // Hooks
  
  useLayoutEffect(() => {
    const selection = selectionRef.current;
    const textarea = textareaRef.current;
    if (!selection || !textarea) return;
    
    textarea.setSelectionRange(selection.start, selection.end);
    textarea.focus();
    selectionRef.current = null;
  });
  
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    
    const keyPressHandler = (ev: KeyboardEvent) => {
      const REPEATABLE_KEYBINDS: KeybindLiteral[] = ["Ctrl+Z", "Ctrl+Shift+Z"];
      
      const kb = eventToLiteral(ev);
      if (!kb) return;
      
      const isTab = kb === "Tab" || kb === "Shift+Tab";
      if (isTab && !keyboardTrapped) return;
      
      const action = actions.get(kb);
      if (!action) return;
      
      ev.preventDefault();
      if (ev.repeat && !REPEATABLE_KEYBINDS.includes(kb)) return;
      
      action(editorMethods);
    };
    
    const focusHandler = () => {
      setKeyboardTrapped(true);
    };
    const blurHandler = () => {
      setKeyboardTrapped(false);
    };
    
    textarea.addEventListener("keydown", keyPressHandler);
    textarea.addEventListener("focus", focusHandler);
    textarea.addEventListener("blur", blurHandler);
    return () => {
      textarea.removeEventListener("keydown", keyPressHandler);
      textarea.removeEventListener("focus", focusHandler);
      textarea.removeEventListener("blur", blurHandler);
    };
  }, [actions, keyboardTrapped, setKeyboardTrapped]);
  
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    
    const inputHandler = () => {
      addHistoryEntry({
        source: textarea.value,
        selection: {
          start: textarea.selectionStart,
          end: textarea.selectionEnd,
        },
      }, true);
    };
    
    const setInitialHistoryEntry = () => {
      const history = editHistoryRef.current;
      // Since this design cannot know exactly when the parent `onSourceChange` gets called for the first time
      // (or ever, lol), this is a workaround.
      if (history.entries.length) return;
      
      addHistoryEntry({
        source: textarea.value,
        selection: {
          start: textarea.selectionStart,
          end: textarea.selectionEnd,
        },
      });
    };
    
    textarea.addEventListener("input", inputHandler);
    textarea.addEventListener("beforeinput", setInitialHistoryEntry);
    return () => {
      textarea.removeEventListener("input", inputHandler);
      textarea.removeEventListener("beforeinput", setInitialHistoryEntry);
    };
  }, [addHistoryEntry]);
  
  return (
    <div className={`wd-editor-toolbar-panel ${className}`} id="wd-editor-toolbar-panel">
      <div
        className="editor-toolbar-wrapper"
        role="toolbar"
        aria-label="Панель инструментов редактора"
      >
        {toolbarButtonGroups.map(buttonGroup => (
          <div
            className={`editor-toolbar-options ${buttonGroup.className}`}
            key={buttonGroup.className}
            role="group"
          >
            {buttonGroup.entry.map(button => (
              <EditorToolbarButton
                className={button.className}
                onClick={() => button.onClick(editorMethods)}
                title={button.title}
                keybind={button.keybind}
                key={`${buttonGroup.className}-${button.className}`}
                disabled={disabled}
              />
            ))}
          </div>
        ))}
      </div>
      <div>
        <p className="editor-toolbar-trap-hint" role="status">
          {keyboardTrapped
            ? "Используйте Escape чтобы вернуться к навигации по странице"
            : "Выделите редактор чтобы использовать панель инструментов"
          }
        </p>
      </div>
      {modalRender()}
    </div>
  );
};


const MittenEditorToolbarPanel = styled(EditorToolbarPanel__Bare)`
  * {
    box-sizing: border-box;
  }

  div {
    height: unset;
  }

  :where(.editor-toolbar-options) {
    display: inline-flex;
    position: relative;
    gap: 2px;
    padding-inline: 6px;
    left: -1px;
    border-left: 1px solid #ccc;
  }

  :where(.editor-toolbar-wrapper) {
    display: flex;
    flex-wrap: wrap;
    overflow-x: clip;
  }
  
  :where(.editor-toolbar-trap-hint) {
    margin-block: 4px;
    font-style: italic;
    font-size: smaller;
  }

  @media (hover: none) {
    .editor-toolbar-trap-hint {
      display: none;
    }
  }

  button {
    --editor-icon-image: url("/-/static/images/editor/mitten-icons/missing.svg");

    height: 32px;
    width: 32px;
    padding: 0;
    margin: 0;
    background: #333;
    position: relative;
    mask-image: var(--editor-icon-image);
    mask-size: 20px;
    mask-repeat: no-repeat;
    mask-position: 6px 6px;
    border: none;
    transition: background-color 0.15s ease-out;
  }

  button:is(:hover, :focus) {
    background: var(--new-side-bar-color, #901);
  }

  ${toolbarButtonGroups.map(buttonGroup => buttonGroup.entry
    .map(button => {
      return css`
        button.${button.className} {
          --editor-icon-image: url(${button.iconPath || "/-/static/images/editor/mitten-icons/missing.svg"});
        }
      `;
    }))
  }
`;


export default MittenEditorToolbarPanel;
