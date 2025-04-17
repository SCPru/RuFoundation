import { useContext } from 'react'
import ConfigContext from './ConfigContext.context'

export function useConfigContext() {
  return useContext(ConfigContext)
}
