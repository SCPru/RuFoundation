import * as React from 'react';
import { useEffect, useState } from 'react';
import useConstCallback from '../util/const-callback';
import styled from "styled-components";
import WikidotModal from "../util/wikidot-modal";
import sleep from "../util/async-sleep";
import {fetchArticle, updateArticle} from "../api/articles";
import {fetchAllTags, FetchAllTagsResponse} from '../api/tags'
import TagEditorComponent from '../components/tag-editor'
import Loader from '../util/loader'


interface Props {
    pageId: string
    isNew?: boolean
    onClose?: () => void
    canCreateTags?: boolean
}


const Styles = styled.div`
.text {  
  &.loading {
    &::after {
      content: ' ';
      position: absolute;
      background: #0000003f;
      z-index: 0;
      left: 0;
      right: 0;
      top: 0;
      bottom: 0;
    }
    .loader {
      position: absolute;
      left: 16px;
      top: 16px;
      z-index: 1;
    }
  }
}
  
.w-tag-editor-container {
  position: relative;
}
  
/* fixes BHL; without table this looks bad */
table.form {
  display: table !important;
}
  
.form tr {
  display: table-row !important;
}
  
.form td, th {
  display: table-cell !important;
}
`;


const ArticleTags: React.FC<Props> = ({ pageId, isNew, onClose, canCreateTags }) => {
    const [tags, setTags] = useState<Array<string>>([]);
    const [allTags, setAllTags] = useState<FetchAllTagsResponse>(null);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [savingSuccess, setSavingSuccess] = useState(false);
    const [error, setError] = useState('');
    const [fatalError, setFatalError] = useState(false);
    
    useEffect(() => {
        setLoading(true);
        Promise.all([fetchArticle(pageId), fetchAllTags()])
        .then(([data, allTags]) => {
            setTags(data.tags);
            setAllTags(allTags);
        })
        .catch(e => {
            setFatalError(true);
            setError(e.error || 'Ошибка связи с сервером');
        })
        .finally(() => {
            setLoading(false);
        });
    }, []);

    const onSubmit = useConstCallback(async (e) => {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }

        setSaving(true);
        setError(undefined);
        setSavingSuccess(false);
        
        const input = {
            pageId: pageId,
            tags: tags
        };

        try {
            await updateArticle(pageId, input);
            setSavingSuccess(true);
            setSaving(false);
            await sleep(1000);
            setSavingSuccess(false);
            window.scrollTo(window.scrollX, 0);
            window.location.reload();
        } catch (e) {
            setSaving(false);
            setFatalError(false);
            setError(e.error || 'Ошибка связи с сервером');
        }
    });

    const onClear = useConstCallback((e) => {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        setTags([]);
    });

    const onCancel = useConstCallback((e) => {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        if (onClose)
            onClose()
    });

    const onCloseError = useConstCallback(() => {
        setError(null);
        if (fatalError) {
            onCancel(null);
        }
    });

    const onChange = useConstCallback((tags: Array<string>) => {
        setTags(tags);
    });

    return (
        <Styles>
            { saving && <WikidotModal isLoading><p>Сохранение...</p></WikidotModal> }
            { savingSuccess && <WikidotModal><p>Успешно сохранено!</p></WikidotModal> }
            { error && (
                <WikidotModal buttons={[{title: 'Закрыть', onClick: onCloseError}]} isError>
                    <p><strong>Ошибка:</strong> {error}</p>
                </WikidotModal>
            ) }
            <a className="action-area-close btn btn-danger" href="#" onClick={onCancel}>Закрыть</a>
            <h1>Теги страницы</h1>
            <p>Теги (метки) это хороший способ для организации содержимого на сайте, для создания "горизонтальной навигации" между связанными по смыслу страницами. Вы можете добавить несколько тегов к каждой из ваших страниц. Читайте подробнее про <a href="http://ru.wikipedia.org/wiki/%D0%A2%D0%B5%D0%B3" target="_blank"> теги</a>, про <a href="http://ru.wikipedia.org/wiki/%D0%9E%D0%B1%D0%BB%D0%B0%D0%BA%D0%BE_%D1%82%D0%B5%D0%B3%D0%BE%D0%B2" target="_blank">облако тегов </a></p>

            <form method="POST" onSubmit={onSubmit}>
                <table className="form">
                    <tbody>
                    <tr>
                        <td>
                            Теги:
                        </td>
                    </tr>
                    <tr>
                        <td className="w-tag-editor-container">
                            { loading && <Loader className="loader" /> }
                            <TagEditorComponent canCreateTags={canCreateTags} tags={tags} allTags={allTags || {categories: [], tags: []}} onChange={onChange} />
                        </td>
                    </tr>
                    </tbody>
                </table>
                <div className="buttons form-actions">
                    <input type="button" className="btn btn-danger" value="Закрыть" onClick={onCancel} />
                    <input type="button" className="btn btn-default" value="Очистить" onClick={onClear} />
                    <input type="button" className="btn btn-primary" value="Сохранить теги" onClick={onSubmit}/>
                </div>
            </form>
        </Styles>
    )
}


export default ArticleTags