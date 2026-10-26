import { useEffect, useState } from 'react'
import { api } from '../api.js'

function ProductRow({ product }) {
  const rgb = product.color
  const [r, g, b] = rgb.slice(1).match(/../g).map((value) => parseInt(value, 16))
  const isLightBackground = r * .299 + g * .587 + b * .114 > 150

  return (
    <tr>
      <th scope="row">
        <div className="product-identity">
          <span className="product-pack" style={{ backgroundColor: rgb, color: isLightBackground ? 'var(--bg)' : 'var(--cream)' }} aria-hidden="true">ЛЧ</span>
          <div className="product-info">
            <span className="product-name">{product.name}</span>
            <span className="product-kind muted">{product.kind}</span>
            <span className="product-mobile-format">{product.pack_format_display} · {product.weight_g} г</span>
            <span className="product-mobile-sku muted">Артикул {product.sku}</span>
          </div>
        </div>
      </th>
      <td><span className="product-format">{product.pack_format_display}</span></td>
      <td>{product.weight_g} г</td>
      <td className="product-sku muted">{product.sku}</td>
    </tr>
  )
}

export default function PromotionalProductsSection() {
  const [products, setProducts] = useState([])
  const [status, setStatus] = useState('loading')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let active = true
    setStatus('loading')
    api('/products/').then((data) => {
      if (!active) return
      setProducts(data)
      setStatus('success')
    }).catch(() => {
      if (active) setStatus('error')
    })
    return () => { active = false }
  }, [attempt])

  return (
    <section id="products" className="section container products-section" aria-labelledby="products-title">
      <h2 id="products-title">Акционная продукция</h2>
      <p className="products-lead muted">В акции участвует чай «Лесная Чашка» из списка — в любом формате</p>
      <div className="products-content" aria-busy={status === 'loading'}>
        {status === 'loading' && <p className="products-state muted" role="status">Загружаем продукцию…</p>}
        {status === 'error' && (
          <div className="products-state" role="alert">
            <p>Не удалось загрузить продукцию.</p>
            <button type="button" className="link-btn" onClick={() => setAttempt((value) => value + 1)}>Попробовать ещё раз</button>
          </div>
        )}
        {status === 'success' && (products.length ? (
          <div className="products-panel">
            <table className="products-table" aria-labelledby="products-title">
              <thead><tr><th scope="col">Продукт</th><th scope="col">Формат</th><th scope="col">Вес</th><th scope="col">Артикул</th></tr></thead>
              <tbody>{products.map((product) => <ProductRow key={product.id} product={product} />)}</tbody>
            </table>
          </div>
        ) : <p className="products-state muted" role="status">Акционная продукция пока не добавлена.</p>)}
      </div>
    </section>
  )
}
