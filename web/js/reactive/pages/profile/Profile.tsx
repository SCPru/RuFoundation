import React from 'react'
import { useConfigContext } from '~reactive/config'
import Page from '~reactive/containers/page'
import * as Styled from './Profile.styles'

const Profile: React.FC = () => {
  /* useEffect(() => {
    window.location.href = '/-/profile/edit'
  }, []) */
  const { user } = useConfigContext()

  return (
    <Page>
      <Styled.Container>
        <Styled.Buttons>
          <Styled.Link href={`/-/users/${user.id}-${user.username}`}>Публичный профиль</Styled.Link>
          <Styled.Separator />
          <Styled.Link href={`/-/profile/edit`}>Редактировать</Styled.Link>
        </Styled.Buttons>
      </Styled.Container>
    </Page>
  )
}

export default Profile
