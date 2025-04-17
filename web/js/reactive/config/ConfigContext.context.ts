import { createContext } from 'react'
import { IConfigContext } from '~reactive/config/ConfigContext.types'

const ConfigContext = createContext<IConfigContext>({} as IConfigContext)

export default ConfigContext
