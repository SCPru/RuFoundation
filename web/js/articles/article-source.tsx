import * as React from 'react';
import { useEffect, useState } from 'react';
import useConstCallback from '../util/const-callback';
import {fetchArticle} from "../api/articles";
import WikidotModal from "../util/wikidot-modal";
import styled from "styled-components";
import Loader from "../util/loader";


interface Props {
    pageId: string
    onClose: () => void
    source?: string
}


const Styles = styled.div<{loading?: boolean}>`
#source-code.loading {
  position: relative;
  min-height: calc(32px + 16px + 16px);
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

textarea {
  width: 100%;
  min-height: 600px;
}
`;


const ArticleSource: React.FC<Props> = ({ pageId, onClose: onCloseDeligate, source: originalSource }) => {
    const [loading, setLoading] = useState(false);
    const [source, setSource] = useState(originalSource);
    const [error, setError] = useState('');

    useEffect(() => {
        loadSource();
    }, []);

    const loadSource = useConstCallback(async () => {
        if (!source) {
            setLoading(true);
            setError(null);
            try {
                const article = await fetchArticle(pageId);
                setError(null);
                setSource(article.source);
            } catch (e) {
                setError(e.error || 'Ошибка связи с сервером');
            } finally {
                setLoading(false);
            }
        }
    });

    const onClose = useConstCallback((e) => {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        if (onCloseDeligate)
            onCloseDeligate();
    });

    const onCloseError = useConstCallback(() => {
        setError(null);
        onClose(null);
    });

    return (
        <Styles>
            { error && (
                <WikidotModal buttons={[{title: 'Закрыть', onClick: onCloseError}]} isError>
                    <p><strong>Ошибка:</strong> {error}</p>
                </WikidotModal>
            ) }
            <a className="action-area-close btn btn-danger" href="#" onClick={onClose}>Закрыть</a>
            <h1>Исходник страницы</h1>
            <div id="source-code" className={`${loading?'loading':''}`}>
                { loading && <Loader className="loader" /> }
                <textarea value={source||''} readOnly />
            </div>
        </Styles>
    )
}


export default ArticleSource