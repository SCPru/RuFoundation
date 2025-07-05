import React, { useEffect, useState } from 'react';
import * as Styled from './Header.styles'

const Header: React.FC = () => {
  const [backLink, setBackLink] = useState('/');
  useEffect(() => {
    const lastPageBefore = sessionStorage.getItem('lastPageBefore');

    if (lastPageBefore) {
      setBackLink(lastPageBefore);
    }
  }, []);

  return (
    <Styled.Container>
      <Styled.FixedWidthContainer>
        <Styled.Heading>Профиль</Styled.Heading>
        <Styled.GoBack href={backLink}>
          <span className="fa fa-arrow-left"></span> Назад на сайт
        </Styled.GoBack>
      </Styled.FixedWidthContainer>
      <Styled.Border />
    </Styled.Container>
  )
}

export default Header
