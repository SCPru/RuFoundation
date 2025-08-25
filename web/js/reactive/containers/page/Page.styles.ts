import styled, { createGlobalStyle, css } from 'styled-components'
import { MOBILE_SIZE } from '~reactive/theme/Theme.consts'

export const RootStyles = createGlobalStyle`
  *, *::before, *::after {
    box-sizing: border-box;
  }
  
  html, body {
    overflow: auto;
    background: ${({ theme }) => theme.windowBackground};
    width: 100%;
    min-height: 100vh;
  }
`

export const Container = styled.div`
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  background: ${({ theme }) => theme.pagePadding};
`

export const HeaderContainer = styled.div`
  background: red;
  position: relative;
  z-index: 1;
`

export const FixedWidthContainer = styled.div<{ hasBorder?: boolean }>`
  position: relative;
  z-index: 0;
  max-width: 1024px;
  width: min(100%, 1024px);
  margin: 0 auto;
  display: flex;
  min-width: 0;
  overflow: hidden;
  flex-grow: 1;

  ${({ hasBorder }) =>
    hasBorder &&
    css`
      box-shadow: 0 0 8px #0000007f;
      padding: 0 5px;

      &:before,
      &:after {
        content: '';
        width: 5px;
        border-left: 1px solid ${({ theme }) => theme.windowStrong};
        border-right: 1px solid ${({ theme }) => theme.windowStrong};
        background: ${({ theme }) => theme.windowPadding};
        position: absolute;
        top: 0;
        bottom: 0;
      }

      &:before {
        left: 0;
      }

      &:after {
        right: 0;
      }
    `};

  @media (max-width: ${MOBILE_SIZE}px) {
    flex-direction: column;
  }
`

export const NavContainer = styled.div`
  background: blue;
  min-width: 240px;
  max-width: 240px;
  flex-shrink: 0;
  flex-grow: 0;
  background: ${({ theme }) => theme.windowBackground};

  @media (max-width: ${MOBILE_SIZE}px) {
    min-width: 0;
    max-width: none;
  }
`

export const ContentContainer = styled.div`
  flex-grow: 1;
  background: ${({ theme }) => theme.windowBackground};
  overflow: auto;
`
