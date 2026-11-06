import React from "react";
import { useCallback, useMemo, useState } from "react";
import EditorModal from "~components/editor-toolbar/modals/base-modal";
import { EditorModalStyleBase } from "~components/editor-toolbar/modals/base-modal";
import type { EditorModalComponent } from "~components/editor-toolbar/modals/base-modal";
import { isInternalLink } from "~util/domain-util";


type LinkType = "external" | "internal";


const LinkModal: EditorModalComponent = ({
  onCancel,
  onSubmit,
}) => {
  const [linkType, setLinkType] = useState<LinkType>("external");
  const [isNewPage, setIsNewPage] = useState<boolean>(false);
  const [link, setLink] = useState<string>("");
  const [title, setTitle] = useState<string>("");
  
  const passedURL = useMemo((): URL | null => URL.parse(link.trim(), window.location.origin), [link]);
  
  const isSameDomain = useMemo((): boolean => isInternalLink(passedURL), [passedURL]);
  
  const createExternalLink = useCallback((): string => {
    return `[${isNewPage ? "*" : ""}${link.trim()} ${title.trim() || "Ссылка"}]`;
  }, [link, title, isNewPage]);
  
  const createInternalLink = useCallback((): string => {
    const pageId = (isSameDomain && passedURL) ? passedURL.pathname.split("/")[1] : link.trim();
    return `[[[${isNewPage ? "*" : ""}${pageId}|${title.trim()}]]]`;
  }, [link, isSameDomain, passedURL, title, isNewPage]);
  
  const createLink = useCallback((): string => {
    const linkFn: Record<LinkType, () => string> = {
      external: createExternalLink,
      internal: createInternalLink,
    };
    return linkFn[linkType]();
  }, [linkType, createExternalLink, createInternalLink]);
  
  return (
    <EditorModal onSubmit={() => onSubmit(createLink())} onCancel={() => onCancel()}>
      <EditorModalStyleBase>
        <p className="editor-modal-header">Мастер вставки ссылок</p>
        <fieldset>
          <legend>Тип вставляемой ссылки</legend>
          <div>
            <label>
              <input
                type="radio"
                name="wd-ed-linkwizard-type"
                value="external"
                checked={linkType === "external"}
                onChange={() => setLinkType("external")}
              />
              Внешняя ссылка
            </label>
            <label>
              <input
                type="radio"
                name="wd-ed-linkwizard-type"
                value="internal"
                checked={linkType === "internal"}
                onChange={() => setLinkType("internal")}
              />
              Внутренняя ссылка
            </label>
          </div>
          <label>
            Открывать в новой вкладке:
            <input
              type="checkbox"
              checked={isNewPage}
              onChange={(ev) => setIsNewPage(ev.target.checked)}
            />
          </label>
        </fieldset>
        <div className="editor-modal-form-grid">
          <label className="editor-modal-subgrid-row">
            Ссылка на страницу:
            <input
              type="text"
              placeholder={(() => {
                const placeholders: Record<LinkType, string> = {
                  external: "https://example.com/",
                  internal: "SCP-173",
                }
                return placeholders[linkType];
              })()}
              size={28}
              onChange={(ev) => setLink(ev.target.value)}
            />
          </label>
          <label className="editor-modal-subgrid-row">
            Текст ссылки:
            <input
              type="text"
              placeholder="Ссылка"
              size={28}
              value={title}
              onChange={(ev) => setTitle(ev.target.value)}
              aria-describedby="wd-ed-linkwizard-link-warning"
            />
          </label>
        </div>
        <div id="wd-ed-linkwizard-link-warning" role="status">
          {(linkType === "internal" && link.trim() && !isSameDomain) && (
            <p>
              Введённая ссылка ведёт на внешний сайт. Будет вставлена полная ссылка.
            </p>
          )}
          {(linkType === "external" && link.trim() && isSameDomain) && (
            <p>
              Введённая ссылка ведёт на этот сайт. Используйте опцию «Внутренняя ссылка».
            </p>
          )}
        </div>
      </EditorModalStyleBase>
    </EditorModal>
  );
};


export default LinkModal;
