import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
type T = 'dark' | 'light'
const Ctx = createContext<{ theme: T; toggle: () => void }>({ theme: 'dark', toggle: () => {} })
export const useTheme = () => useContext(Ctx)
export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<T>(() => (document.documentElement.dataset.theme as T) || 'dark')
  useEffect(() => { document.documentElement.dataset.theme = theme; try { localStorage.setItem('pt-theme', theme) } catch {} }, [theme])
  return <Ctx.Provider value={{ theme, toggle: () => setTheme(t => (t === 'dark' ? 'light' : 'dark')) }}>{children}</Ctx.Provider>
}
