import styled, { css } from 'styled-components'

export const Container = styled.div`
  max-width: 600px;
  margin: 20px auto;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
  background-color: #fff;
  /*@media (prefers-color-scheme: dark) {
        box-shadow: 0px 4px 20px 10px rgba(0, 0, 0, 0.1);
    }*/
  @media screen and (max-height: 740px) {
    box-shadow: none;
    margin: 0;
  }
`

export const List = styled.div`
  padding: 16px;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
  gap: 8px;
`

export const FilterContainer = styled.div`
  display: flex;
  justify-content: center;
  margin: 16px;
  border-bottom: 1px solid ${({ theme }) => theme.windowStrong};
`

export const RadioLabel = styled.label<{ checked: boolean }>`
  padding: 8px 16px;
  position: relative;
  top: 1px;
  border-bottom: 1px solid transparent;
  cursor: pointer;
  font-weight: 500;

  ${({ checked }) =>
    checked &&
    css`
      background: ${({ theme }) => `${theme.windowPadding}7f`};
      border-bottom: 1px solid ${({ theme }) => theme.uiSelection};
    `};

  &:hover {
    background: ${({ theme }) => `${theme.windowPadding}7f`};
  }
`

export const RadioInput = styled.input`
  display: none;
`

export const EmptyMessage = styled.div`
  text-align: center;
  font-size: 24px;
  line-height: 28px;
  font-weight: 500;
  padding: 16px;
`

export const LoaderContainer = styled.div`
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
`
