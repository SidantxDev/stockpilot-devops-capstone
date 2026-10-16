import { formatINR } from '../api.js'

export default function KpiCards({ stats, loading }) {
  const cards = [
    { label: 'Products', value: stats?.total_products, hint: 'Active SKUs' },
    { label: 'Units on hand', value: stats?.total_units?.toLocaleString('en-IN'), hint: 'Across all locations' },
    { label: 'Inventory value', value: stats && formatINR(stats.inventory_value), hint: 'At unit cost' },
    {
      label: 'Needs reorder',
      value: stats && stats.low_stock + stats.out_of_stock,
      hint: stats ? `${stats.low_stock} low · ${stats.out_of_stock} out` : '—',
      tone: stats && stats.low_stock + stats.out_of_stock > 0 ? 'warn' : '',
    },
  ]

  return (
    <section className="kpis" aria-label="Key metrics">
      {cards.map((c) => (
        <article key={c.label} className={`card kpi ${c.tone || ''}`}>
          <p className="kpi-label">{c.label}</p>
          <p className="kpi-value">{loading || c.value === undefined ? <span className="skeleton" /> : c.value}</p>
          <p className="kpi-hint">{c.hint}</p>
        </article>
      ))}
    </section>
  )
}
