import { useCallback, useEffect, useState } from 'react'
import { api } from './api.js'
import Sidebar from './components/Sidebar.jsx'
import KpiCards from './components/KpiCards.jsx'
import ProductTable from './components/ProductTable.jsx'
import ProductModal from './components/ProductModal.jsx'
import AdjustModal from './components/AdjustModal.jsx'
import ActivityFeed from './components/ActivityFeed.jsx'
import CategoryBreakdown from './components/CategoryBreakdown.jsx'

const STATUS_FILTERS = [
  { value: '', label: 'All' },
  { value: 'in_stock', label: 'In stock' },
  { value: 'low_stock', label: 'Low stock' },
  { value: 'out_of_stock', label: 'Out of stock' },
]

export default function App() {
  const [products, setProducts] = useState([])
  const [stats, setStats] = useState(null)
  const [movements, setMovements] = useState([])
  const [status, setStatus] = useState('')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')
  const [editing, setEditing] = useState(null) // null = closed, {} = new, product = edit
  const [adjusting, setAdjusting] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const [list, s, m] = await Promise.all([
        api.listProducts({ status, q: search.trim() }),
        api.stats(),
        api.movements(8),
      ])
      setProducts(list)
      setStats(s)
      setMovements(m)
      setError('')
    } catch (err) {
      setError(err.message || 'Backend unreachable')
    } finally {
      setLoading(false)
    }
  }, [status, search])

  useEffect(() => {
    const timer = setTimeout(refresh, 250) // debounce search typing
    return () => clearTimeout(timer)
  }, [refresh])

  useEffect(() => {
    if (!toast) return
    const timer = setTimeout(() => setToast(''), 3000)
    return () => clearTimeout(timer)
  }, [toast])

  const run = async (action, message) => {
    await action()
    setToast(message)
    await refresh()
  }

  const handleSave = (data) =>
    run(
      () => (editing?.id ? api.updateProduct(editing.id, data) : api.createProduct(data)),
      editing?.id ? `Updated ${data.name}` : `Added ${data.name}`,
    ).then(() => setEditing(null))

  const handleAdjust = (data) =>
    run(() => api.adjustStock(adjusting.id, data), `Stock updated for ${adjusting.name}`).then(() =>
      setAdjusting(null),
    )

  const handleDelete = async (product) => {
    if (!window.confirm(`Delete ${product.name} (${product.sku})? This also removes its stock history.`)) return
    try {
      await run(() => api.deleteProduct(product.id), `Deleted ${product.name}`)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="layout">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} lowStock={stats?.low_stock ?? 0} />

      <main className="main">
        <header className="topbar">
          <button className="icon-btn menu-btn" aria-label="Open menu" onClick={() => setSidebarOpen(true)}>
            ☰
          </button>
          <div>
            <p className="eyebrow">Main warehouse · Bengaluru</p>
            <h1>Inventory overview</h1>
          </div>
          <button className="btn btn-primary" onClick={() => setEditing({})}>
            + Add product
          </button>
        </header>

        {error && (
          <div className="alert" role="alert">
            <strong>Can’t reach the StockPilot API.</strong> {error}
            <button className="btn btn-ghost" onClick={refresh}>
              Retry
            </button>
          </div>
        )}

        <KpiCards stats={stats} loading={loading} />

        <div className="grid">
          <section className="card table-card">
            <div className="card-head">
              <h2>Products</h2>
              <div className="filters">
                <input
                  className="search"
                  type="search"
                  placeholder="Search name, SKU, supplier…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  aria-label="Search products"
                />
                <div className="segmented" role="tablist" aria-label="Filter by stock status">
                  {STATUS_FILTERS.map((f) => (
                    <button
                      key={f.value}
                      role="tab"
                      aria-selected={status === f.value}
                      className={status === f.value ? 'active' : ''}
                      onClick={() => setStatus(f.value)}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <ProductTable
              products={products}
              loading={loading}
              onEdit={setEditing}
              onAdjust={setAdjusting}
              onDelete={handleDelete}
            />
          </section>

          <aside className="side-col">
            <ActivityFeed movements={movements} />
            <CategoryBreakdown categories={stats?.categories} />
          </aside>
        </div>
      </main>

      {editing && <ProductModal product={editing} onSave={handleSave} onClose={() => setEditing(null)} />}
      {adjusting && <AdjustModal product={adjusting} onSave={handleAdjust} onClose={() => setAdjusting(null)} />}
      {toast && (
        <div className="toast" role="status">
          {toast}
        </div>
      )}
    </div>
  )
}
