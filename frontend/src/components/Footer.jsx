export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-inner">
        <div className="footer-links">
          <a href="#rules">Правила акции</a>
          <a href="#privacy">Политика конфиденциальности</a>
          <a href="mailto:support@example.com">Обратная связь</a>
        </div>
        <p className="legal">
          Организатор акции — ООО «Пример» (вымышленная компания, сайт для тестового задания). Период покупки товара
          и регистрации чеков: с 1 декабря 2026 по 31 января 2027. Срок выдачи призов — до 28 февраля 2027.
          Количество призов ограничено. Подробные условия — в правилах акции.
        </p>
      </div>
    </footer>
  )
}
