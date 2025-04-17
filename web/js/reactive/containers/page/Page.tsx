import React from 'react'
import Header from './Header'
import Navigation from './Navigation'
import * as Styled from './Page.styles'

export const Page: React.FC = ({ children }) => {
  return (
    <Styled.Container>
      <Styled.RootStyles />
      <Styled.HeaderContainer>
        <Header />
      </Styled.HeaderContainer>
      <Styled.FixedWidthContainer>
        <Styled.NavContainer>
          <Navigation />
        </Styled.NavContainer>
        <Styled.ContentContainer>{children}</Styled.ContentContainer>
      </Styled.FixedWidthContainer>
    </Styled.Container>
  )
}

export default Page
