import React from 'react'
import { Paths } from '~reactive/paths'
import * as Styled from './Navigation.styles'

const Navigation: React.FC = () => {
  return (
    <Styled.Container>
      <Styled.Link to={Paths.profile}>Редактировать профиль</Styled.Link>
      <Styled.Link to={Paths.notifications}>Уведомления</Styled.Link>
    </Styled.Container>
  )
}

export default Navigation
