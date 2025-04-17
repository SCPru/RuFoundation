import styled from 'styled-components'
import { MOBILE_SIZE } from '~reactive/theme/Theme.consts'

export const Container = styled.div`
  background:
    repeating-linear-gradient(45deg, rgba(255, 255, 255, 0.062745098), transparent 4px),
    linear-gradient(to bottom, ${({ theme }) => theme.headingStart}, ${({ theme }) => theme.headingEnd});
  box-shadow: 0 -1px 3px #0000007f inset;
  min-height: 80px;
  color: white;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: space-around;
  min-width: 0;
  overflow: hidden;
`

export const FixedWidthContainer = styled.div`
  max-width: 1024px;
  width: min(100%, 1024px);
  margin: auto;

  @media (max-width: ${MOBILE_SIZE}px) {
    padding: 0 16px;
  }
`

export const Heading = styled.h1`
  font-size: 20px;
  font-weight: 600;
  text-shadow: 1px 1px 3px black;
  color: white;
`

export const Border = styled.div`
  width: 100%;
  height: 5px;
  border-top: 1px solid ${({ theme }) => theme.windowStrong};
  border-bottom: 1px solid ${({ theme }) => theme.windowStrong};
  background: ${({ theme }) => theme.windowPadding};
`
