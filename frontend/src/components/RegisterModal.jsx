import { useState } from 'react'
import { api, fieldError, formError } from '../api.js'
import { useApp } from '../app-context.jsx'
import { Button, Checkbox, Field, Modal } from './ui.jsx'

/** Маска телефона: +7 (900) 000-00-00 */
export function formatPhone(raw) {
  let digits = raw.replace(/\D/g, '')
  if (digits.startsWith('8') || digits.startsWith('7')) digits = digits.slice(1)
  digits = digits.slice(0, 10)
  let out = '+7'
  if (digits.length > 0) out += ' (' + digits.slice(0, 3)
  if (digits.length >= 3) out += ')'
  if (digits.length > 3) out += ' ' + digits.slice(3, 6)
  if (digits.length > 6) out += '-' + digits.slice(6, 8)
  if (digits.length > 8) out += '-' + digits.slice(8, 10)
  return out
}

const EMPTY = { first_name: '', last_name: '', email: '', phone: '', password: '' }

export default function RegisterModal() {
  const { closeModal, openModal, setUser } = useApp()
  const [form, setForm] = useState(EMPTY)
  const [agreeRules, setAgreeRules] = useState(false)
  const [agreePd, setAgreePd] = useState(false)
  const [errors, setErrors] = useState({})
  const [common, setCommon] = useState('')
  const [sending, setSending] = useState(false)

  const set = (name) => (e) => {
    const value = name === 'phone' ? formatPhone(e.target.value) : e.target.value
    setForm({ ...form, [name]: value })
    setErrors({ ...errors, [name]: undefined })
  }

  const submit = async (e) => {
    e.preventDefault()
    setSending(true)
    setCommon('')
    try {
      const profile = await api('/auth/register/', {
        method: 'POST',
        body: { ...form, agree_rules: agreeRules, agree_pd: agreePd },
      })
      setUser(profile)
      openModal('receipt')
    } catch (err) {
      setErrors(err.data || {})
      setCommon(formError(err))
    } finally {
      setSending(false)
    }
  }

  return (
    <Modal title="Регистрация" subtitle="Зарегистрируйтесь, чтобы загружать чеки и получать призы" onClose={closeModal}>
      <form onSubmit={submit} noValidate>
        <Field label="Имя" value={form.first_name} onChange={set('first_name')} error={fieldError(errors, 'first_name')} autoComplete="given-name" placeholder="Мария" />
        <Field label="Фамилия" value={form.last_name} onChange={set('last_name')} error={fieldError(errors, 'last_name')} autoComplete="family-name" placeholder="Иванова" />
        <Field label="E-mail" type="email" value={form.email} onChange={set('email')} error={fieldError(errors, 'email')} autoComplete="email" placeholder="example@mail.ru" />
        <Field label="Телефон" hint="на него придут призы" type="tel" value={form.phone} onChange={set('phone')} error={fieldError(errors, 'phone')} autoComplete="tel" placeholder="+7 (___) ___-__-__" />
        <Field label="Пароль" hint="не менее 8 символов" type="password" value={form.password} onChange={set('password')} error={fieldError(errors, 'password')} autoComplete="new-password" placeholder="••••••••" />
        <Checkbox checked={agreeRules} onChange={(v) => { setAgreeRules(v); setErrors({ ...errors, agree_rules: undefined }) }} error={fieldError(errors, 'agree_rules')}>
          Я согласен с <a href="#rules">правилами акции</a>
        </Checkbox>
        <Checkbox checked={agreePd} onChange={(v) => { setAgreePd(v); setErrors({ ...errors, agree_pd: undefined }) }} error={fieldError(errors, 'agree_pd')}>
          Я даю согласие на обработку <a href="#privacy">персональных данных</a>
        </Checkbox>
        {common && <p className="form-error">{common}</p>}
        <Button type="submit" className="btn-block" disabled={sending}>
          {sending ? 'Отправляем…' : 'Зарегистрироваться'}
        </Button>
      </form>
      <p className="popup-foot">
        Есть профиль? <button type="button" className="link-btn" onClick={() => openModal('login')}>Войти</button>
      </p>
    </Modal>
  )
}
