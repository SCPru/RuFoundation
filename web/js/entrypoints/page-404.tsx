import * as React from 'react'
import { useState } from 'react'
import useConstCallback from '../util/const-callback'

interface Props {
  pageId?: string
  pathParams?: { [key: string]: string }
}

const Page404: React.FC<Props> = ({ pageId, pathParams }) => {
  const [isCreate, setIsCreate] = useState(!!pathParams['edit'])

  const onCreate = useConstCallback(e => {
    e.preventDefault()
    e.stopPropagation()
    setIsCreate(true)
    ;(window as any)._openNewEditor(() => {
      setIsCreate(false)
    })
  })

  if (!isCreate) {
    return (
      <>
        <p id="404-message">
          Запрашиваемая вами страница <em>{pageId}</em> не существует.
        </p>
        <ul id="create-it-now-link">
          <li>
            <a href="#" onClick={onCreate}>
              Создать страницу
            </a>
          </li>
        </ul>
      </>
    )
  } else {
    return <></>
  }
}

export default Page404
