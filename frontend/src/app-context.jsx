import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { api, ApiError, ensureCsrf } from './api.js'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loaded, setLoaded] = useState(false)
  // Открытый попап: 'register' | 'login' | 'receipt' | null
  const [modal, setModal] = useState(null)

  const refresh = useCallback(async () => {
    try {
      setUser(await api('/me/'))
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) setUser(null)
      else throw err
    }
  }, [])

  useEffect(() => {
    ensureCsrf()
      .then(refresh)
      .catch(() => setUser(null))
      .finally(() => setLoaded(true))
  }, [refresh])

  const logout = useCallback(async () => {
    await api('/auth/logout/', { method: 'POST' })
    setUser(null)
    await ensureCsrf()
  }, [])

  // «Зарегистрировать чек» без входа ведёт на регистрацию.
  const openReceipt = useCallback(() => setModal(user ? 'receipt' : 'register'), [user])

  const value = { user, setUser, loaded, refresh, logout, modal, openModal: setModal, closeModal: () => setModal(null), openReceipt }
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  return useContext(AppContext)
}
