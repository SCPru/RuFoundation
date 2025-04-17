import React from 'react'
import * as Styled from './Header.styles'

const Header: React.FC = () => {
  return (
    <Styled.Container>
      <Styled.FixedWidthContainer>
        <Styled.Heading>Профиль</Styled.Heading>
      </Styled.FixedWidthContainer>
      <Styled.Border />
    </Styled.Container>
  )
}

export default Header
