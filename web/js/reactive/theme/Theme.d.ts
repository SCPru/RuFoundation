import 'styled-components'

import { ReactTheme } from './Theme.types'

declare module 'styled-components' {
  export interface DefaultTheme extends ReactTheme {}
}
