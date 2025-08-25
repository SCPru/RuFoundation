import * as React from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { ThemeProvider } from 'styled-components'
import ConfigContextProvider from '~reactive/config'
import { IConfigContext } from '~reactive/config/ConfigContext.types'
import Notifications from '~reactive/pages/notifications'
import Profile from '~reactive/pages/profile'
import Search from '~reactive/pages/search'
import { Paths } from '~reactive/paths'
import { SYSTEM_THEME } from '~reactive/theme/Theme.consts'

export default function ReactivePage() {
  const reactiveRoot: HTMLElement = document.querySelector('#reactive-root')
  const config: IConfigContext = JSON.parse(reactiveRoot.dataset.config)

  if (config.user.type !== 'user') {
    window.location.href = `/-/login?to=${encodeURIComponent(window.location.href)}`
    return null
  }

  return (
    <ConfigContextProvider config={config}>
      <ThemeProvider theme={SYSTEM_THEME}>
        <BrowserRouter basename="/-">
          <Routes>
            <Route path={Paths.profile} element={<Profile />} />
            <Route path={`${Paths.notifications}/*`} element={<Notifications />} />
            <Route path={Paths.search} element={<Search />} />
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </ConfigContextProvider>
  )
}
