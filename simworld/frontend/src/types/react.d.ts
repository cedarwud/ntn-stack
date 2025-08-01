// Global React types for the project
import type { FC, MutableRefObject, MouseEvent, ChangeEvent, FormEvent, SyntheticEvent, CSSProperties, RefObject } from 'react'

// Re-export commonly used React types globally
declare global {
  type ReactFC<T = object> = FC<T>
  type ReactRef<T> = MutableRefObject<T>
  type ReactRefObject<T> = RefObject<T>
  type ReactMouseEvent<T = Element> = MouseEvent<T>
  type ReactChangeEvent<T = Element> = ChangeEvent<T>
  type ReactFormEvent<T = Element> = FormEvent<T>
  type ReactSyntheticEvent<T = Element> = SyntheticEvent<T>
  type ReactCSSProperties = CSSProperties
}

export {} 