import React from "react";
import { useCallback, useState, useEffect, useSyncExternalStore } from "react";
import styled from "styled-components";
import EditorModal from "~components/editor-toolbar/modals/base-modal";
import { EditorModalStyleBase } from "~components/editor-toolbar/modals/base-modal";
import { fetchArticleFiles } from "~api/files";
import { APIError } from "~util/fetch-util";
import type { EditorModalComponent } from "~components/editor-toolbar/modals/base-modal";
import type { ArticleFile } from "~api/files";
import Loader from "~util/loader";
import { isInternalLink } from "~util/domain-util";


type FileLoadingStaus = "pending" | "success" | "error";

type ImageLinkType = "freeLink" | "file";
type ImageMarkupType = "legacy" | "include";
type ImageAlign = "left" | "center" | "right";


interface FileStoreBase {
  status: FileLoadingStaus,
  files: ArticleFile[] | null,
  errorMessage: string | null,
}

interface FileStoreSuccess extends FileStoreBase {
  status: "success",
  files: ArticleFile[],
  errorMessage: null,
}

interface FileStorePending extends FileStoreBase {
  status: "pending",
  files: null,
  errorMessage: null,
}

interface FileStoreError extends FileStoreBase {
  status: "error",
  files: null,
  errorMessage: string,
}

type FileStoreState = FileStoreSuccess | FileStorePending | FileStoreError;


// An overcomplicated solution of a simple problem, but I'm a sucker for OOP so
class FileStore {
  private readonly listeners: Set<() => void> = new Set();
  private state: FileStoreState = {
    status: "pending",
    files: null,
    errorMessage: null,
  };
  
  private emit = () => this.listeners.forEach((listener) => listener());
  
  public subscribe = (listener: () => void): () => void => {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  };
  
  public getSnapshot = () => this.state;
  
  public setState = (state: FileStoreState) => {
    this.state = state;
    this.emit();
  };
  
  public load = (pageId: string, force: boolean = false) => {
    if (this.state.status === "success" && !force) return;
    
    this.setState({
      status: "pending",
      files: null,
      errorMessage: null,
    });
    
    fetchArticleFiles(pageId)
      .then(response => this.setState({
        status: "success",
        files: response.files.filter(file => file.mimeType.startsWith("image")),
        errorMessage: null,
      }))
      .catch((error: unknown) => {
        const errorMessage = (error instanceof APIError)
          ? error.message || "Ошибка связи с сервером"
          : "Неизвестная ошибка";
        this.setState({
          status: "error",
          files: null,
          errorMessage: errorMessage,
        });
      });
  };
}


const fileStore = new FileStore();

const ImageModalStyle = styled(EditorModalStyleBase)`
  .image-modal-files-container {
    width: fit-content;
    margin-inline: auto;
    padding-inline: 1em;
  }

  .image-modal-buttons {
    display: flex;
    justify-content: flex-end;
    margin-bottom: var(--editor-modal-gap);
  }
`;


const LEGACY_ALIGN: Record<ImageAlign, string> = {
  left: "limg",
  center: "cimg",
  right: "rimg",
};
const DEFAULT_WIDTH = "300px";
const DEFAULT_FILE_LINK = "Ссылка";


const ImageModal: EditorModalComponent = ({
  onSubmit,
  onCancel,
  pageId,
}) => {
  const fileStoreState = useSyncExternalStore(fileStore.subscribe, fileStore.getSnapshot);
  const [imageLinkType, setImageLinkType] = useState<ImageLinkType>("freeLink");
  const [selectedFileLink, setSelectedFileLink] = useState<string>("");
  const [markupType, setMarkupType] = useState<ImageMarkupType>("include");
  const [caption, setCaption] = useState<string>("");
  const [align, setAlign] = useState<ImageAlign>("right");
  const [width, setWidth] = useState<string>("");
  
  const getProcessedInputs = useCallback(() => {
    return {
      fileLink: encodeURI(selectedFileLink.trim() || DEFAULT_FILE_LINK),
      align: align,
      caption: caption.trim(),
      width: width.trim() || DEFAULT_WIDTH,
    }
  }, [selectedFileLink, align, caption, width]);
  
  const createLegacyImage = useCallback((): string => {
    const { fileLink, align, caption, width } = getProcessedInputs();
    
    const lines: string[] = [
      `[[div_ class="${LEGACY_ALIGN[align]}"]]`,
      `[[image ${fileLink} style="width: ${width}"]]`,
    ];
    if (caption) {
      lines.push(`[[span]]${caption.replaceAll("\n", " _\n")}[[/span]]`);
    }
    lines.push("[[/div]]");
    return lines.join("\n");
  }, [getProcessedInputs]);
  
  const createIncludeImage = useCallback((): string => {
    const { fileLink, align, caption, width } = getProcessedInputs();
    
    return [
      "[[include component:image-block",
      `  | name=${fileLink}`,
      `  | align=${align}`,
      `  | caption=${caption}`,
      `  | width=${width}`,
      "]]"
    ].join("\n");
    }, [getProcessedInputs]);
  
  const createImage = useCallback((): string => {
    const imageFn: Record<ImageMarkupType, () => string> = {
      include: createIncludeImage,
      legacy: createLegacyImage,
    };
    return imageFn[markupType]();
  }, [markupType, createLegacyImage, createIncludeImage]);
  
  const onRefreshClick = useCallback(() => {
    if (!pageId) return;
    setSelectedFileLink("");
    fileStore.load(pageId, true);
  }, [pageId]);
  
  useEffect(() => {
    if (!pageId) return;
    fileStore.load(pageId);
  }, []);
  
  useEffect(() => {
    if (fileStoreState.status === "success" && fileStoreState.files.length) {
      setSelectedFileLink(fileStoreState.files[0].name);
    }
  }, [fileStoreState.files]);
  
  return (
    <EditorModal onSubmit={() => onSubmit(createImage())} onCancel={() => onCancel()}>
      <ImageModalStyle>
        <p className="editor-modal-header">Мастер вставки изображений</p>
        <fieldset>
          <legend>Тип вставляемого изображения</legend>
          <div>
            <label>
              <input
                type="radio"
                name="wd-ed-imagewizard-type"
                value="freeLink"
                checked={imageLinkType === "freeLink"}
                onChange={() => setImageLinkType("freeLink")}
              />
              Произвольная ссылка
            </label>
            {pageId && (
              <label>
                <input
                  type="radio"
                  name="wd-ed-imagewizard-type"
                  value="file"
                  checked={imageLinkType === "file"}
                  onChange={() => setImageLinkType("file")}
                />
                Файл статьи
              </label>
            )}
          </div>
        </fieldset>
        
        {imageLinkType === "freeLink" && (
          <>
            <div className="editor-modal-form-grid">
              <label className="editor-modal-subgrid-row">
                Ссылка:
                <input
                  type="text"
                  name="wd-ed-imagewizard-link"
                  value={selectedFileLink}
                  onChange={ev => setSelectedFileLink(ev.target.value)}
                  placeholder={DEFAULT_FILE_LINK}
                  size={28}
                  aria-describedby="wd-ed-imagewizard-link-warning"
                />
              </label>
            </div>
            <div id="wd-ed-imagewizard-link-warning" role="status">
              {!isInternalLink(URL.parse(selectedFileLink, window.location.origin)) && (
                <p>
                  Введённая ссылка ведёт на внешний сайт. Это может привести к <a
                    href="https://ru.wikipedia.org/wiki/%D0%92%D1%8B%D0%BC%D0%B8%D1%80%D0%B0%D0%BD%D0%B8%D0%B5_%D1%81%D1%81%D1%8B%D0%BB%D0%BE%D0%BA"
                    target="_blank"
                  > вымиранию ссылки</a> и утрате доступа к изображению.
                </p>
              )}
            </div>
          </>
        )}
        
        {imageLinkType === "file" && (
          <div>
            <div className="image-modal-buttons">
              <button
                type="button"
                onClick={onRefreshClick}
                disabled={fileStoreState.status === "pending"}
              >Перезагрузить
              </button>
            </div>
            
            {fileStoreState.status === "pending" && (
              <div className="editor-modal-loader-container">
                <Loader/>
              </div>
            )}
            
            {fileStoreState.status === "error" && (
              <div className="image-modal-error-container" role="alert">
                <p>{`К сожалению, что-то пошло не так: ${fileStoreState.errorMessage}`}</p>
              </div>
            )}
            
            {fileStoreState.status === "success" && (
              <div className="image-modal-files-container editor-modal-scroll-area">
                <div className="editor-modal-choice-list" role="radiogroup">
                  {fileStoreState.files.length ? (
                    fileStoreState.files.map(image => (
                      <label key={image.name}>
                        <input
                          type="radio"
                          name="image-modal-file-select"
                          value={image.name}
                          checked={image.name === selectedFileLink}
                          onChange={ev => setSelectedFileLink(ev.target.value)}
                        />
                        {image.name}
                      </label>
                    ))
                  ) : <p>На данной странице нет ни одного файла изображений.</p>}
                </div>
              </div>
            )}
          </div>
        )}
        
        <h4>Дополнительные опции</h4>
        <div className="editor-modal-margin">
          <label>
            Подпись:
            <textarea
              name="wd-ed-imagewizard-caption"
              value={caption}
              onChange={ev => setCaption(ev.target.value)}
              onInput={ev => {
                if (!CSS.supports("field-sizing", "content")) {
                  const textarea = ev.currentTarget;
                  textarea.style.height = "auto";
                  textarea.style.height = `${textarea.scrollHeight}px`;
                }
              }}
              placeholder="Описание изображения"
            />
          </label>
          <div className="editor-modal-form-grid">
            <label className="editor-modal-subgrid-row">
              Тип синтаксиса:
              <select
                id="wd-ed-imagewizard-markup-select"
                value={markupType}
                onChange={ev => setMarkupType(ev.target.value as ImageMarkupType)}
              >
                <option value="legacy">Классический (rimg/cimg/limg)</option>
                <option value="include">Стандартный блок с изображением</option>
              </select>
            </label>
            <label className="editor-modal-subgrid-row">
              Выравнивание:
              <select
                id="wd-ed-imagewizard-align-select"
                value={align}
                onChange={ev => setAlign(ev.target.value as ImageAlign)}
              >
                <option value="left">Слева</option>
                <option value="center">По центру</option>
                <option value="right">Справа</option>
              </select>
            </label>
            <label className="editor-modal-subgrid-row">
              Ширина:
              <input
                type="text"
                value={width}
                onChange={ev => setWidth(ev.target.value)}
                placeholder={DEFAULT_WIDTH}
              />
            </label>
          </div>
        </div>
        <div className="editor-modal-hint">
          <p>
            <b>Подсказка</b>: поле «Ширина» принимает в себя <a
            href="https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/width#syntax"
            target="_blank"
          > любое валидное в CSS значение для ширины</a>.
          </p>
        </div>
      </ImageModalStyle>
    </EditorModal>
  );
};


export default ImageModal;
