import React from 'react'
import * as Styled from './Header.styles'

const Header: React.FC = () => {
  return (
    <Styled.Container>
      <Styled.FixedWidthContainer>
        <Styled.Heading>Профиль</Styled.Heading>
        <Styled.GoBack href="/">
          <span className="fa fa-arrow-left"></span> Назад на сайт
        </Styled.GoBack>
      </Styled.FixedWidthContainer>
      <Styled.Border />
    </Styled.Container>
  )
}

export default Header
