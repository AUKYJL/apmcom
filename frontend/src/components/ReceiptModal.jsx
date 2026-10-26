import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, fieldError, formError } from '../api.js'
import { useApp } from '../app-context.jsx'
import { Button, Checkbox, Field, Modal } from './ui.jsx'

const MAX_PHOTOS = 5
const MAX_MB = 10

function formatDate(iso) {
  const [y, m, d] = iso.split('-')
  return `${d}.${m}.${y}`
}

/** Те же правила, что и на сервере, чтобы ошибки было видно до отправки. */
function validateManual(f) {
  const e = {}
  if (!f.purchased_at) e.purchased_at = 'Укажите дату и время покупки'
  if (!f.amount.trim()) e.amount = 'Укажите сумму чека'
  else if (!/^\d+([.,]\d{1,2})?$/.test(f.amount.replace(/\s/g, ''))) e.amount = 'Сумма в формате 1248,90'
  if (!/^\d{16}$/.test(f.fn)) e.fn = 'ФН — 16 цифр'
  if (!/^\d{1,10}$/.test(f.fd)) e.fd = 'ФД — от 1 до 10 цифр'
  if (!/^\d{8,10}$/.test(f.fp)) e.fp = 'Проверьте ФП: от 8 до 10 цифр'
  return e
}

export default function ReceiptModal() {
  const { closeModal, refresh, user } = useApp()
  const navigate = useNavigate()
  const fileInput = useRef(null)
  const [mode, setMode] = useState('manual')
  const [form, setForm] = useState({ purchased_at: '', amount: '', fn: '', fd: '', fp: '' })
  const [photos, setPhotos] = useState([])
  const [agree, setAgree] = useState(true)
  const [errors, setErrors] = useState({})
  const [common, setCommon] = useState('')
  const [sending, setSending] = useState(false)
  const [done, setDone] = useState(false)

  const promo = user?.promo
  const subtitle = promo ? `Принимаются чеки с ${formatDate(promo.start)} по ${formatDate(promo.end)}` : ''

  // Ссылки на превью освобождаем при удалении фото и при закрытии попапа.
  const photosRef = useRef(photos)
  photosRef.current = photos
  useEffect(() => () => photosRef.current.forEach((p) => URL.revokeObjectURL(p.url)), [])

  const set = (name, digitsOnly) => (e) => {
    const value = digitsOnly ? e.target.value.replace(/\D/g, '') : e.target.value
    setForm({ ...form, [name]: value })
    setErrors({ ...errors, [name]: undefined })
  }

  const addPhotos = (fileList) => {
    const next = [...photos]
    let problem = ''
    for (const file of fileList) {
      if (next.length >= MAX_PHOTOS) { problem = `Не более ${MAX_PHOTOS} фото`; break }
      if (!file.type.startsWith('image/')) { problem = 'Можно загрузить только изображения'; continue }
      if (file.size > MAX_MB * 1024 * 1024) { problem = `Файл ${file.name} больше ${MAX_MB} МБ`; continue }
      next.push({ file, url: URL.createObjectURL(file) })
    }
    setPhotos(next)
    setErrors({ ...errors, photos: problem || undefined })
  }

  const removePhoto = (index) => {
    URL.revokeObjectURL(photos[index].url)
    setPhotos(photos.filter((_, i) => i !== index))
  }

  const submit = async (e) => {
    e.preventDefault()
    setCommon('')
    const clientErrors = mode === 'manual' ? validateManual(form) : (photos.length ? {} : { photos: 'Добавьте хотя бы одно фото чека' })
    if (!agree) clientErrors.agree = 'Нужно согласие с правилами акции'
    setErrors(clientErrors)
    if (Object.keys(clientErrors).length) return

    const data = new FormData()
    data.append('source', mode)
    if (mode === 'manual') {
      data.append('purchased_at', form.purchased_at)
      data.append('amount', form.amount.replace(/\s/g, '').replace(',', '.'))
      data.append('fn', form.fn)
      data.append('fd', form.fd)
      data.append('fp', form.fp)
    }
    photos.forEach((p) => data.append('photos', p.file))

    setSending(true)
    try {
      await api('/receipts/', { method: 'POST', body: data })
      await refresh()
      setDone(true)
    } catch (err) {
      setErrors(err.data || {})
      setCommon(formError(err))
    } finally {
      setSending(false)
    }
  }

  if (done) {
    return (
      <Modal title="Чек отправлен" subtitle="Мы проверим его в течение 24 часов и начислим баллы и приз" onClose={closeModal}>
        <div className="success-mark" aria-hidden="true">✓</div>
        <Button className="btn-block" onClick={() => { closeModal(); navigate('/lk') }}>В личный кабинет</Button>
      </Modal>
    )
  }

  return (
    <Modal title="Регистрация чека" subtitle={subtitle} onClose={closeModal}>
      <div className="switch" role="tablist">
        <button type="button" role="tab" aria-selected={mode === 'photo'} className={mode === 'photo' ? 'on' : ''} onClick={() => setMode('photo')}>Фото чека</button>
        <button type="button" role="tab" aria-selected={mode === 'manual'} className={mode === 'manual' ? 'on' : ''} onClick={() => setMode('manual')}>Ввести вручную</button>
      </div>

      <form onSubmit={submit} noValidate>
        {mode === 'manual' && (
          <>
            <div className="row2">
              <Field label="Дата и время" type="datetime-local" value={form.purchased_at} onChange={set('purchased_at')} error={fieldError(errors, 'purchased_at')} />
              <Field label="Сумма чека" hint="с копейками" inputMode="decimal" value={form.amount} onChange={set('amount')} error={fieldError(errors, 'amount')} placeholder="1 248,90" />
            </div>
            <Field label="ФН" hint="16 цифр" inputMode="numeric" maxLength={16} value={form.fn} onChange={set('fn', true)} error={fieldError(errors, 'fn')} placeholder="9960440300123456" />
            <div className="row2">
              <Field label="ФД" hint="до 10 цифр" inputMode="numeric" maxLength={10} value={form.fd} onChange={set('fd', true)} error={fieldError(errors, 'fd')} placeholder="48213" />
              <Field label="ФП" hint="до 10 цифр" inputMode="numeric" maxLength={10} value={form.fp} onChange={set('fp', true)} error={fieldError(errors, 'fp')} placeholder="1234567890" />
            </div>
          </>
        )}

        <button type="button" className={`upload ${errors.photos ? 'upload-error' : ''}`} onClick={() => fileInput.current?.click()}>
          <span className="upload-icon" aria-hidden="true">+</span>
          <span>
            <b>{mode === 'photo' ? 'Загрузить фото чека' : 'Добавить фото чека'}</b>
            <span>JPG или PNG, до {MAX_MB} МБ, не более {MAX_PHOTOS} файлов{mode === 'manual' ? ' (необязательно)' : ''}</span>
          </span>
        </button>
        <input ref={fileInput} type="file" accept="image/*" multiple hidden onChange={(e) => { addPhotos(e.target.files); e.target.value = '' }} />
        {errors.photos && <p className="field-error upload-msg">{fieldError(errors, 'photos')}</p>}

        {photos.length > 0 && (
          <div className="thumbs">
            {photos.map((p, i) => (
              <div className="thumb" key={p.url}>
                <img src={p.url} alt={`Фото чека ${i + 1}`} />
                <button type="button" onClick={() => removePhoto(i)} aria-label="Удалить фото">✕</button>
              </div>
            ))}
          </div>
        )}

        <Checkbox checked={agree} onChange={(v) => { setAgree(v); setErrors({ ...errors, agree: undefined }) }} error={errors.agree}>
          Я согласен с <a href="#rules">правилами акции</a>
        </Checkbox>
        {common && <p className="form-error">{common}</p>}
        <Button type="submit" className="btn-block" disabled={sending}>{sending ? 'Отправляем…' : 'Отправить'}</Button>
      </form>
    </Modal>
  )
}
