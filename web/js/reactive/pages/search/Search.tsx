import React, { useRef, useState } from 'react'
import { sprintf } from 'sprintf-js'
import { useTheme } from 'styled-components'
import { RatingMode } from '~api/rate'
import { fetchSearch, SearchResults } from '~api/search'
import Page from '~reactive/containers/page'
import { highlightWords } from '~reactive/pages/search/Search.utils'
import useConstCallback from '~util/const-callback'
import formatDate from '~util/date-format'
import UserView from '~util/user-view'
import * as Styled from './Search.styles'
import WikidotModal from '~util/wikidot-modal'

export const Search: React.FC = () => {
  const theme = useTheme()
  const [searchText, setSearchText] = useState('')
  const searchRef = useRef<HTMLInputElement | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const [isSource, setIsSource] = useState(false)

  const [lastSearchText, setLastSearchText] = useState('')
  const [lastSource, setLastSource] = useState(false)
  const [searchResults, setSearchResults] = useState<SearchResults | undefined>(undefined)
  const [error, setError] = useState<string | undefined>(undefined)

  const handleSearchChange = useConstCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchText(event.target.value)
  })

  const handleSourceChange = useConstCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setIsSource(event.target.checked)
  })

  const handleSearchSubmit = useConstCallback(async (event: React.FormEvent) => {
    event.stopPropagation()
    event.preventDefault()
    if (isSearching) {
      return
    }
    if (!searchText.trim()) {
      return
    }
    setIsSearching(true)
    try {
      const results = await fetchSearch(searchText, {
        mode: isSource ? 'source' : 'plain'
      })
      setLastSearchText(searchText)
      setLastSource(isSource)
      setSearchResults(results)
      containerRef.current?.scrollTo(0, 0)
      setError(undefined)
    } catch (e: any) {
      setError(e.error || 'Ошибка связи с сервером')
    } finally {
      setIsSearching(false)
    }
  })

  const renderRating = useConstCallback((rating: number, mode: RatingMode) => {
    if (mode === 'updown') {
      return sprintf('%+d', rating)
    }
    if (mode === 'stars') {
      return sprintf('%.1f', rating)
    }
    return '—'
  })

  const handleLoadMore = useConstCallback(async (event: React.MouseEvent) => {
    event.stopPropagation()
    event.preventDefault()
    if (isSearching) {
      return
    }
    if (!lastSearchText || !searchResults) {
      return
    }
    setIsSearching(true)
    try {
      const results = await fetchSearch(lastSearchText, {
        cursor: searchResults.cursor,
        mode: lastSource ? 'source' : 'plain'
      })
      setSearchResults({
        results: [...searchResults.results, ...results.results],
        cursor: results.cursor,
      })
      setError(undefined)
    } catch (e: any) {
      setError(e.error || 'Ошибка связи с сервером')
    } finally {
      setIsSearching(false)
    }
  })

  const onCloseError = useConstCallback(() => {
    setError(undefined)
  })

  return (
    <Page title="Поиск по сайту">
      {error && (
        <WikidotModal buttons={[{ title: 'Закрыть', onClick: onCloseError }]} isError>
          <p>
            <strong>Ошибка:</strong> {error}
          </p>
        </WikidotModal>
      )}
      <Styled.Container ref={containerRef}>
        <Styled.SearchFieldContainer>
          <Styled.SearchFieldWrapper onSubmit={handleSearchSubmit} isDisabled={isSearching}>
            <Styled.SearchField placeholder="Ваш запрос" ref={searchRef} value={searchText} onChange={handleSearchChange} disabled={isSearching} />
            <Styled.LoaderContainer>
              <Styled.SearchSubmit disabled={isSearching} onClick={handleSearchSubmit} value={isSearching ? '' : 'Искать'} />
              {isSearching && <Styled.Loader color={theme.uiSelectionForeground} />}
            </Styled.LoaderContainer>
          </Styled.SearchFieldWrapper>
          <Styled.CheckboxContainer>
            <label>
              <input type="checkbox" checked={isSource} onChange={handleSourceChange} />
              <span>
                Поиск по исходнику
              </span>
            </label>
          </Styled.CheckboxContainer>
        </Styled.SearchFieldContainer>
        <Styled.SearchResultsWrapper>
          {searchResults?.results?.map((article, index) => {
            return (
              <Styled.SearchResult key={index}>
                <Styled.SearchResultTitle>
                  <a href={`${window.location.origin}/${article.pageId}`} target="_blank">{highlightWords(article.title, article.words)}</a>
                </Styled.SearchResultTitle>
                <Styled.SearchResultSlug>
                  {article.pageId}
                </Styled.SearchResultSlug>
                <Styled.SearchResultMeta>
                  <Styled.SearchResultMetaItem>
                    <Styled.SearchResultMetaKey>От:</Styled.SearchResultMetaKey>
                    <Styled.SearchResultMetaValue>
                      <UserView data={article.createdBy} />
                    </Styled.SearchResultMetaValue>
                  </Styled.SearchResultMetaItem>
                  <Styled.SearchResultMetaItem>
                    <Styled.SearchResultMetaKey>Создана:</Styled.SearchResultMetaKey>
                    <Styled.SearchResultMetaValue>{formatDate(new Date(article.createdAt))}</Styled.SearchResultMetaValue>
                  </Styled.SearchResultMetaItem>
                  <Styled.SearchResultMetaItem>
                    <Styled.SearchResultMetaKey>Последнее изменение:</Styled.SearchResultMetaKey>
                    <Styled.SearchResultMetaValue>{formatDate(new Date(article.updatedAt))}</Styled.SearchResultMetaValue>
                  </Styled.SearchResultMetaItem>
                  <Styled.SearchResultMetaItem>
                    <Styled.SearchResultMetaKey>Рейтинг:</Styled.SearchResultMetaKey>
                    <Styled.SearchResultMetaValue>
                      {renderRating(article.rating.value, article.rating.mode)}
                      {article.rating.votes > 0 && (
                        <>
                          {' '}
                          от {article.rating.votes} (популярность: {sprintf('%d%%', article.rating.popularity)})
                        </>
                      )}
                    </Styled.SearchResultMetaValue>
                  </Styled.SearchResultMetaItem>
                </Styled.SearchResultMeta>
                {article.excerpts.length > 0 && (
                  <Styled.SearchResultExcerpts>
                    {article.excerpts.map((x, i, a) => (
                      <Styled.SearchResultExcerpt>
                        {' ...'}
                        {highlightWords(x, article.words)}
                        {'... '}
                      </Styled.SearchResultExcerpt>
                    ))}
                  </Styled.SearchResultExcerpts>
                )}
              </Styled.SearchResult>
            )
          })}
          {searchResults && searchResults.results.length > 0 && searchResults.results.length % 25 === 0 && (
            <Styled.Button onClick={handleLoadMore} isDisabled={isSearching} disabled={isSearching}>
              {isSearching ? <Styled.Loader color={theme.uiSelectionForeground} /> : 'Ещё результаты'}
            </Styled.Button>
          )}
        </Styled.SearchResultsWrapper>
      </Styled.Container>
    </Page>
  )
}

export default Search
