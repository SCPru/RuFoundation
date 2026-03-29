import { NavLink } from 'react-router-dom'
import styled from 'styled-components'
import { MOBILE_SIZE } from '~reactive/theme/Theme.consts'

export const Container = styled.div`
  background: ${({ theme }) => theme.uiBackground};
  border-right: 1px solid ${({ theme }) => theme.windowStrong};
  height: 100%;
  width: 100%;

  @media (max-width: ${MOBILE_SIZE}px) {
    display: flex;

    & > * {
      flex: 1 1 0;
      white-space: nowrap;
    }
  }
`

export const Link = styled(NavLink)`
  display: block;
  padding: 16px 8px;
  color: ${({ theme }) => theme.uiForeground};

  &:link,
  &:hover,
  &:active,
  &:visited {
    text-decoration: none;
  }

  &:hover {
    background: ${({ theme }) => `${theme.uiSelection}2f`};
  }

  &.active,
  &.active:hover {
    background: ${({ theme }) => theme.uiSelection};
    color: ${({ theme }) => theme.uiSelectionForeground};
  }

  @media (max-width: ${MOBILE_SIZE}px) {
    text-align: center;
  }
`
