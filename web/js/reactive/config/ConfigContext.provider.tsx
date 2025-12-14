import React from 'react'
import ConfigContext from './ConfigContext.context'
import { IConfigContext } from './ConfigContext.types'

interface Props {
  config: IConfigContext
  children?: React.ReactNode
}

const ConfigContextProvider: React.FC<Props> = ({ config, children }) => {
  return <ConfigContext.Provider value={config}>{children}</ConfigContext.Provider>
}

export default ConfigContextProvider
