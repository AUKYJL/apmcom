import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { Button } from '../components/ui.jsx'
import { useApp } from '../app-context.jsx'
import PromotionalProductsSection from '../components/PromotionalProductsSection.jsx'

const STEPS = [
  { title: 'Купите', text: 'любой чай «Лесная Чашка» в магазинах-участниках' },
  { title: 'Зарегистрируйте', text: 'чек на сайте: загрузите фото или введите данные вручную' },
  { title: 'Получите', text: 'гарантированный приз от 50 ₽ до 300 ₽ на телефон' },
  { title: 'Участвуйте', text: 'в еженедельных розыгрышах и розыгрыше главного приза' },
]

const GUARANTEED = [50, 70, 100, 150, 200, 300]

const FAQ = [
  {
    q: 'Что нужно сделать для участия в акции?',
    a: 'Купите любой чай «Лесная Чашка» в магазинах-участниках, зарегистрируйтесь на сайте и загрузите фото чека или введите его данные вручную. Чек проверяется в течение 24 часов.',
  },
  {
    q: 'Какие чеки принимаются?',
    a: 'Кассовые чеки с покупкой чая «Лесная Чашка», совершённой с 1 декабря 2026 по 31 января 2027. На чеке должны читаться дата, сумма, ФН, ФД и ФП.',
  },
  {
    q: 'Сколько чеков можно зарегистрировать?',
    a: 'Количество не ограничено, но каждый чек можно зарегистрировать только один раз. Чек на сумму больше 1000 ₽ приносит 2 балла, остальные — 1 балл.',
  },
  {
    q: 'Как и когда определяются победители?',
    a: 'Еженедельные розыгрыши проходят по пятницам среди всех принятых чеков за неделю. Главный приз разыгрывается 5 февраля 2027 среди участников с тремя и более принятыми чеками.',
  },
  {
    q: 'Когда придёт приз на телефон?',
    a: 'Гарантированный приз зачисляется на номер из профиля в течение 5 рабочих дней после того, как чек принят.',
  },
  {
    q: 'Почему мой чек отклонён?',
    a: 'Чаще всего из-за даты покупки вне периода акции, нечитаемого фото или если такой чек уже зарегистрирован. Причина указана в личном кабинете.',
  },
]

function Faq() {
  const [open, setOpen] = useState(0)
  return (
    <div className="faq">
      {FAQ.map((item, i) => (
        <div key={item.q} className={`faq-item ${open === i ? 'faq-open' : ''}`}>
          <button type="button" className="faq-q" onClick={() => setOpen(open === i ? -1 : i)} aria-expanded={open === i}>
            {item.q}
            <span className="faq-sign" aria-hidden="true">{open === i ? '−' : '+'}</span>
          </button>
          {open === i && <p className="faq-a">{item.a}</p>}
        </div>
      ))}
    </div>
  )
}

export default function Home() {
  const { openReceipt } = useApp()
  const { hash } = useLocation()

  useEffect(() => {
    if (!hash) return
    document.getElementById(hash.slice(1))?.scrollIntoView({ behavior: 'smooth' })
  }, [hash])

  return (
    <>
      <section className="hero container">
        <div className="hero-text">
          <p className="dates">с 1 декабря 2026 по 31 января 2027</p>
          <h1>Согрейтесь <em>зимой</em> с Лесной Чашкой</h1>
          <p className="hero-lead">Покупайте чай «Лесная Чашка», регистрируйте чеки и получайте призы каждую неделю</p>
          <Button className="hero-btn" onClick={openReceipt}>Зарегистрировать чек</Button>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="pack pack-1"><span className="pack-name">Лесная<br />Чашка</span><span className="pack-sub">чабрец · малина</span></div>
          <div className="pack pack-2"><span className="pack-name">Лесная<br />Чашка</span><span className="pack-sub">облепиха</span></div>
        </div>
        <Button className="hero-btn-mobile" onClick={openReceipt}>Зарегистрировать чек</Button>
      </section>

      <section id="how" className="section container">
        <h2>Как участвовать</h2>
        <div className="steps">
          {STEPS.map((step, i) => (
            <div className="step" key={step.title}>
              <span className="step-num">{i + 1}</span>
              <div>
                <h3 className="step-title">{step.title}</h3>
                <p className="step-text">{step.text}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <PromotionalProductsSection />

      <section id="prizes" className="section-band">
        <div className="section container">
          <h2>Призы</h2>
          <div className="prizes">
            <div className="prize">
              <h3 className="prize-label">Гарантированные призы</h3>
              <div className="chips">{GUARANTEED.map((v) => <span className="chip" key={v}>{v} ₽</span>)}</div>
              <p className="prize-desc">Пополнение баланса мобильного телефона за каждый принятый чек</p>
            </div>
            <div className="prize">
              <h3 className="prize-label">Еженедельный розыгрыш</h3>
              <div className="prize-card pc-green"><b>5 000 ₽</b><span>сертификат</span></div>
              <p className="prize-desc">Сертификат в магазин посуды. 10 победителей каждую неделю</p>
            </div>
            <div className="prize">
              <h3 className="prize-label">Главный приз</h3>
              <div className="prize-card pc-berry"><b>100 000 ₽</b><span>на банковскую карту</span></div>
              <p className="prize-desc">Разыгрывается среди всех участников, зарегистрировавших 3 и более чеков</p>
            </div>
          </div>
          <Button onClick={openReceipt}>Зарегистрировать чек</Button>
        </div>
      </section>

      <section id="faq" className="section container">
        <h2>Вопрос-ответ</h2>
        <Faq />
        <a className="btn btn-outline" href="mailto:support@example.com">Задать вопрос</a>
      </section>
    </>
  )
}
