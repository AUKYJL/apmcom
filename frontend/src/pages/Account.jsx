import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api.js'
import { Button } from '../components/ui.jsx'
import { useApp } from '../app-context.jsx'

const STATUS_CLASS = { accepted: 's-ok', pending: 's-wait', rejected: 's-bad' }

function plural(n, one, few, many) {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return one
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return few
  return many
}

function formatPhone(phone) {
  const d = phone.replace(/\D/g, '')
  if (d.length !== 11) return phone
  return `+7 ${d.slice(1, 4)} ${d.slice(4, 7)}-${d.slice(7, 9)}-${d.slice(9)}`
}

const formatDate = (iso) => new Date(iso).toLocaleDateString('ru-RU')
const formatRub = (n) => `${Number(n).toLocaleString('ru-RU')} ₽`

function prizeText(r) {
  if (r.status === 'rejected') return r.reject_reason || 'Чек отклонён'
  if (r.status === 'pending') return '—'
  return r.prize_amount ? `${formatRub(r.prize_amount)} на телефон` : 'Участвует в розыгрыше'
}

export default function Account() {
  const { user, loaded, logout, openModal, openReceipt } = useApp()
  const navigate = useNavigate()
  const [receipts, setReceipts] = useState(null)

  useEffect(() => {
    if (!loaded) return
    if (!user) {
      navigate('/', { replace: true })
      openModal('login')
      return
    }
    api('/receipts/').then(setReceipts).catch(() => setReceipts([]))
  }, [loaded, user, navigate, openModal])

  if (!user) return null
  const s = user.stats

  const onLogout = async () => {
    await logout()
    navigate('/')
  }

  return (
    <div className="account container">
      <h1 className="page-title">Личный кабинет</h1>

      <div className="profile">
        <div className="user-card">
          <b>{user.first_name} {user.last_name}</b>
          <span className="muted">{user.email}</span>
          <span className="muted">{formatPhone(user.phone)}</span>
          <div className="user-links">
            {user.is_staff && <a href="/admin/">Админка</a>}
            <button type="button" className="link-btn" onClick={onLogout}>Выйти</button>
          </div>
        </div>
        <div className="stats">
          <div className="stat"><b>{s.uploaded}</b><span>{plural(s.uploaded, 'чек загружен', 'чека загружено', 'чеков загружено')}</span></div>
          <div className="stat"><b>{s.accepted}</b><span>{plural(s.accepted, 'чек принят', 'чека принято', 'чеков принято')}</span></div>
          <div className="stat"><b>{s.rejected}</b><span>{plural(s.rejected, 'чек отклонён', 'чека отклонено', 'чеков отклонено')}</span></div>
          <div className="stat stat-hl"><b>{s.points}</b><span>{plural(s.points, 'балл', 'балла', 'баллов')} на балансе</span></div>
          <div className="stat stat-wide"><b>{formatRub(s.prizes_total)}</b><span>призов на телефон</span></div>
        </div>
      </div>

      <div className="center"><Button onClick={openReceipt}>Зарегистрировать чек</Button></div>

      <section className="account-section">
        <h2>Мои чеки</h2>
        {receipts === null && <p className="muted center">Загружаем…</p>}
        {receipts?.length === 0 && (
          <div className="empty">
            <p>Вы ещё не загрузили ни одного чека</p>
          </div>
        )}
        {receipts?.length > 0 && (
          <div className="rtable" role="table">
            <div className="rrow rhead" role="row">
              <span role="columnheader">№ чека (ФД)</span>
              <span role="columnheader">Дата загрузки</span>
              <span role="columnheader">Баллы</span>
              <span role="columnheader">Статус</span>
              <span role="columnheader">Приз</span>
            </div>
            {receipts.map((r) => (
              <div className="rrow" role="row" key={r.id}>
                <span className="r-num" role="cell">№ {r.fd || r.id}</span>
                <span className="r-date" role="cell">{formatDate(r.created_at)}</span>
                <span className="r-points" role="cell">{r.status === 'accepted' ? r.points : '—'}<i> {r.status === 'accepted' ? plural(r.points, 'балл', 'балла', 'баллов') : ''}</i></span>
                <span className="r-status" role="cell"><span className={`status ${STATUS_CLASS[r.status]}`}>{r.status_display}</span></span>
                <span className={`r-prize ${r.status === 'rejected' ? 'muted' : ''}`} role="cell">{prizeText(r)}</span>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="account-section">
        <h2>Мои призы</h2>
        <div className="myprizes">
          <div className="myprize">
            <h3>Гарантированные</h3>
            <b>{formatRub(s.prizes_total)}</b>
            <p>Начисляется на номер {formatPhone(user.phone)}. Зачисление в течение 5 рабочих дней.</p>
          </div>
          <div className="myprize">
            <h3>Еженедельный розыгрыш</h3>
            <b>{s.accepted > 0 ? 'Участвуете' : 'Пока нет'}</b>
            <p>{s.accepted > 0 ? 'Чем больше баллов, тем больше шансов на сертификат 5 000 ₽.' : 'Зарегистрируйте чек, чтобы участвовать в розыгрыше.'}</p>
          </div>
          <div className="myprize">
            <h3>Главный приз</h3>
            <b>{s.main_prize_progress} из {s.main_prize_required} чеков</b>
            <p>{s.main_prize_progress >= s.main_prize_required ? 'Вы участвуете в розыгрыше 100 000 ₽. Итоги — 5 февраля 2027.' : 'Нужно 3 принятых чека, чтобы участвовать в розыгрыше 100 000 ₽.'}</p>
          </div>
        </div>
      </section>
    </div>
  )
}
