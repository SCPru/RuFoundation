import React from 'react'
import Header from './Header'
import * as Styled from './Page.styles'

interface Props {
  title: string
  hasBorder?: boolean
}

export const Page: React.FC<Props> = ({ children, title, hasBorder = false }) => {
  return (
    <Styled.Container>
      <Styled.RootStyles />
      <Styled.HeaderContainer>
        <Header title={title} />
      </Styled.HeaderContainer>
      <Styled.FixedWidthContainer hasBorder={hasBorder}>{children}</Styled.FixedWidthContainer>
    </Styled.Container>
  )
}

export default Page
