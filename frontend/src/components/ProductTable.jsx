import { formatINR } from '../api.js'

const STATUS_LABEL = { in_stock: 'In stock', low_stock: 'Low stock', out_of_stock: 'Out of stock' }

export function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{STATUS_LABEL[status]}</span>
}

export default function ProductTable({ products, loading, onEdit, onAdjust, onDelete }) {
  if (loading) {
    return (
      <div className="empty">
        <span className="spinner" aria-hidden="true" /> Loading inventory…
      </div>
    )
  }
  if (!products.length) {
    return <div className="empty">No products match this view. Try another filter or add a product.</div>
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Product</th>
            <th>Category</th>
            <th className="num">Qty</th>
            <th className="num">Unit price</th>
            <th>Status</th>
            <th aria-label="Actions" />
          </tr>
        </thead>
        <tbody>
          {products.map((p) => (
            <tr key={p.id}>
              <td data-label="Product" className="product-cell">
                <div>
                  <strong>{p.name}</strong>
                  <small>
                    {p.sku}
                    {p.location ? ` · ${p.location}` : ''}
                  </small>
                </div>
              </td>
              <td data-label="Category">{p.category}</td>
              <td data-label="Qty" className="num">
                <div>
                  {p.quantity}
                  <small>reorder at {p.reorder_level}</small>
                </div>
              </td>
              <td data-label="Unit price" className="num">
                {formatINR(p.unit_price)}
              </td>
              <td data-label="Status">
                <StatusBadge status={p.stock_status} />
              </td>
              <td className="actions">
                <button className="btn btn-small" onClick={() => onAdjust(p)}>
                  Adjust
                </button>
                <button className="btn btn-small btn-ghost" onClick={() => onEdit(p)}>
                  Edit
                </button>
                <button className="btn btn-small btn-danger" onClick={() => onDelete(p)} aria-label={`Delete ${p.name}`}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
