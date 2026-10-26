import { useEffect } from 'react'

export function Logo() {
  return (
    <span className="logo">
      <svg className="logo-icon" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <circle cx="24" cy="24" r="24" fill="#E8A33D" />
        <path d="M12 20h20v6a10 10 0 0 1-20 0v-6z" fill="#1E3A2B" />
        <path d="M32 22h3a4 4 0 0 1 0 8h-3" stroke="#1E3A2B" strokeWidth="2.5" />
        <path d="M20 10c-2 3 2 4 0 7M25 10c-2 3 2 4 0 7" stroke="#1E3A2B" strokeWidth="2" strokeLinecap="round" />
      </svg>
      <span className="logo-text">
        Лесная Чашка<span>травяной чай</span>
      </span>
    </span>
  )
}

export function Button({ children, variant = 'primary', arrow = true, className = '', ...props }) {
  return (
    <button type="button" className={`btn ${variant === 'outline' ? 'btn-outline' : ''} ${className}`} {...props}>
      {children}
      {arrow && variant !== 'outline' && <span className="btn-arrow" aria-hidden="true">→</span>}
    </button>
  )
}

export function Modal({ title, subtitle, onClose, children }) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    document.body.classList.add('no-scroll')
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.classList.remove('no-scroll')
    }
  }, [onClose])

  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="popup" role="dialog" aria-modal="true" aria-label={title}>
        <button type="button" className="popup-close" onClick={onClose} aria-label="Закрыть">✕</button>
        <h2 className="popup-title">{title}</h2>
        {subtitle && <p className="popup-sub">{subtitle}</p>}
        {children}
      </div>
    </div>
  )
}

export function Field({ label, hint, error, className = '', ...inputProps }) {
  return (
    <label className={`field ${className}`}>
      <span className="field-top">
        {label}
        {hint && <span>{hint}</span>}
      </span>
      <input className={`input ${error ? 'input-error' : ''}`} {...inputProps} />
      {error && <span className="field-error">{error}</span>}
    </label>
  )
}

export function Checkbox({ checked, onChange, error, children }) {
  return (
    <div className="check-wrap">
      <label className="check">
        <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
        <span className="box" aria-hidden="true">{checked ? '✓' : ''}</span>
        <span>{children}</span>
      </label>
      {error && <span className="field-error">{error}</span>}
    </div>
  )
}
