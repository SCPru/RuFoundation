import styled, { css } from 'styled-components'
import BaseLoader from '~util/loader'

export const Container = styled.div`
  width: 100%;
  overflow: auto;
`

export const SearchFieldContainer = styled.div`
  padding: 8px 0;
  position: sticky;
  top: 0;
  background: ${({ theme }) => theme.pagePadding};

  &:after {
    content: '';
    position: absolute;
    left: 0;
    bottom: -16px;
    right: 0;
    height: 16px;
    background: linear-gradient(to bottom, ${({ theme }) => theme.pagePadding}, transparent);
  }
`

export const SearchFieldWrapper = styled.form<{ isDisabled?: boolean }>`
  padding: 8px;
  border: 1px solid ${({ theme }) => theme.uiBorder};
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  opacity: 0.8;
  background: ${({ theme }) => theme.uiBackground};
  &:has(:hover),
  &:has(:focus) {
    opacity: 1;
  }

  ${({ isDisabled }) =>
    isDisabled &&
    css`
      opacity: 0.6;
      filter: saturate(0%);

      input[type='submit'] {
        cursor: not-allowed;
      }
    `};
`

export const SearchField = styled.input.attrs({
  type: 'text',
})`
  flex-grow: 1;
  border: none;
  height: 32px;
  outline: none;
  font-size: 14px;
`

export const SearchSubmit = styled.input.attrs({
  type: 'submit',
})`
  background: ${({ theme }) => theme.uiSelection};
  color: ${({ theme }) => theme.uiSelectionForeground};
  padding: 12px 32px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  width: 128px;
  text-align: center;

  &:hover {
    background: ${({ theme }) => theme.uiSelectionHighlight};
    color: ${({ theme }) => theme.uiSelectionForeground};
  }
`

export const LoaderContainer = styled.div`
  position: relative;
`

export const Loader = styled(BaseLoader).attrs({ size: 24 })`
  position: absolute;
  left: calc(50% - 12px);
  top: calc(50% - 12px);
  pointer-events: none;
`

export const SearchResultsWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
  padding-bottom: 8px;
`

export const SearchResult = styled.div`
  min-width: 0;
  border: ${({ theme }) => theme.uiBorder};
  background: ${({ theme }) => theme.windowBackground};
  padding: 8px;

  .highlight {
    color: red !important;
    font-weight: 600;
  }
`

export const SearchResultTitle = styled.div`
  font-size: 16px;
  line-height: 18px;
  a {
    color: ${({ theme }) => theme.primary};
    border-bottom: 1px dotted ${({ theme }) => theme.primary};
  }
`

export const SearchResultSlug = styled.span`
  margin-top: 8px;
  background: ${({ theme }) => theme.windowStrong}7f;
  padding: 4px;
  border-radius: 8px;
  font-family: monospace;
  display: inline-block;
`

export const SearchResultExcerpts = styled.div`
  margin-top: 16px;
  font-size: 11px;
  line-height: 14px;
`

export const SearchResultExcerpt = styled.span``

export const SearchResultMeta = styled.dl`
  display: flex;
  flex-wrap: wrap;
  min-width: 0;
  gap: 8px;
`

export const SearchResultMetaItem = styled.div``

export const SearchResultMetaKey = styled.span`
  font-weight: 600;
  padding-right: 4px;
`

export const SearchResultMetaValue = styled.span``

export const Button = styled.button<{ isDisabled?: boolean }>`
  background: ${({ theme }) => theme.uiSelection};
  color: ${({ theme }) => theme.uiSelectionForeground};
  padding: 12px 32px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  width: 100%;
  text-align: center;
  margin: 0;
  height: 48px;
  position: relative;

  &:hover {
    background: ${({ theme }) => theme.uiSelectionHighlight};
    color: ${({ theme }) => theme.uiSelectionForeground};
  }

  ${({ isDisabled }) =>
    isDisabled &&
    css`
      opacity: 0.6;
      filter: saturate(0%);
      cursor: not-allowed;
    `};
`

export const CheckboxContainer = styled.div`
  margin-top: 8px;
  cursor: pointer;
  user-select: none;
  padding: 8px;
  border-radius: 8px;
  background: ${({ theme }) => theme.windowBackground}7f;
  display: inline-block;
  
  label {
    cursor: pointer;
  }
`