import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Logo } from './ui.jsx'
import { useApp } from '../app-context.jsx'

const NAV = [
  { href: '/#how', label: 'Как участвовать' },
  { href: '/#prizes', label: 'Призы' },
  { href: '/#faq', label: 'Вопрос-ответ' },
]

function UserIcon({ color }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="8" r="4" stroke={color} strokeWidth="2" />
      <path d="M4 21c1-4 4.5-6 8-6s7 2 8 6" stroke={color} strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

export default function Header() {
  const { user, openModal } = useApp()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const onAccount = pathname === '/lk'

  const goAccount = () => {
    setMenuOpen(false)
    if (user) navigate('/lk')
    else openModal('login')
  }

  return (
    <header className="header">
      <div className="container header-row">
        <Link to="/" onClick={() => setMenuOpen(false)} aria-label="На главную"><Logo /></Link>
        <nav className="nav">
          {NAV.map((item) => <Link key={item.href} to={item.href}>{item.label}</Link>)}
        </nav>
        <button type="button" className={`lk-btn ${onAccount ? 'lk-btn-active' : ''}`} onClick={goAccount}>
          Личный кабинет
        </button>
        <div className="header-mobile">
          <button type="button" className={`icon-btn ${onAccount ? 'icon-btn-fill' : ''}`} onClick={goAccount} aria-label="Личный кабинет">
            <UserIcon color={onAccount ? '#1E3A2B' : '#E8A33D'} />
          </button>
          <button type="button" className="icon-btn icon-btn-fill" onClick={() => setMenuOpen(!menuOpen)} aria-label="Меню" aria-expanded={menuOpen}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              {menuOpen
                ? <path d="M6 6l12 12M18 6L6 18" stroke="#1E3A2B" strokeWidth="2.4" strokeLinecap="round" />
                : <path d="M4 6h16M4 12h16M4 18h16" stroke="#1E3A2B" strokeWidth="2.4" strokeLinecap="round" />}
            </svg>
          </button>
        </div>
      </div>
      {menuOpen && (
        <nav className="mobile-menu">
          {NAV.map((item) => <Link key={item.href} to={item.href} onClick={() => setMenuOpen(false)}>{item.label}</Link>)}
          <button type="button" className="mobile-menu-lk" onClick={goAccount}>Личный кабинет</button>
        </nav>
      )}
    </header>
  )
}
