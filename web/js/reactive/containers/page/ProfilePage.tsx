import React from 'react'
import Navigation from './Navigation'
import Page from './Page'
import * as Styled from './Page.styles'

export const ProfilePage: React.FC = ({ children }) => {
  return (
    <Page title="Профиль" hasBorder={true}>
      <Styled.NavContainer>
        <Navigation />
      </Styled.NavContainer>
      <Styled.ContentContainer>{children}</Styled.ContentContainer>
    </Page>
  )
}

export default ProfilePage
