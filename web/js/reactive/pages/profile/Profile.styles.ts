import styled from 'styled-components'

export const Container = styled.div`
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
`

export const Link = styled.a`
  background: ${({ theme }) => theme.uiSelection};
  color: ${({ theme }) => theme.uiSelectionForeground};
  display: inline-block;
  padding: 8px 16px;
  white-space: nowrap;
  border-radius: 4px;

  &:hover,
  &:active,
  &:visited {
    background: ${({ theme }) => theme.uiSelection};
    color: ${({ theme }) => theme.uiSelectionForeground};
    text-decoration: none;
  }

  &:hover {
    background: ${({ theme }) => theme.uiSelectionHighlight};
  }
`

export const Buttons = styled.div`
  display: flex;
  gap: 8px;
  & > * {
    flex: 1 1 0;
  }
`

export const Separator = styled.div`
  align-self: stretch;
  border-left: 1px solid ${({ theme }) => theme.windowStrong};
`
