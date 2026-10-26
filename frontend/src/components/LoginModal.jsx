import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, fieldError, formError } from '../api.js'
import { useApp } from '../app-context.jsx'
import { Button, Field, Modal } from './ui.jsx'

export default function LoginModal() {
  const { closeModal, openModal, setUser } = useApp()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState({})
  const [common, setCommon] = useState('')
  const [sending, setSending] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setSending(true)
    setCommon('')
    try {
      setUser(await api('/auth/login/', { method: 'POST', body: { email, password } }))
      closeModal()
      navigate('/lk')
    } catch (err) {
      setErrors(err.data || {})
      setCommon(formError(err))
    } finally {
      setSending(false)
    }
  }

  return (
    <Modal title="Вход" subtitle="Войдите, чтобы загружать чеки и следить за призами" onClose={closeModal}>
      <form onSubmit={submit} noValidate>
        <Field label="E-mail" type="email" value={email} onChange={(e) => setEmail(e.target.value)} error={fieldError(errors, 'email')} autoComplete="email" placeholder="example@mail.ru" />
        <Field label="Пароль" type="password" value={password} onChange={(e) => setPassword(e.target.value)} error={fieldError(errors, 'password')} autoComplete="current-password" placeholder="••••••••" />
        {common && <p className="form-error">{common}</p>}
        <Button type="submit" className="btn-block" disabled={sending}>
          {sending ? 'Входим…' : 'Войти'}
        </Button>
      </form>
      <p className="popup-foot">
        Нет профиля? <button type="button" className="link-btn" onClick={() => openModal('register')}>Зарегистрироваться</button>
      </p>
    </Modal>
  )
}
