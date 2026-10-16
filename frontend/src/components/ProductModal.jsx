import { useState } from 'react'
import Modal from './Modal.jsx'

const CATEGORIES = ['Electronics', 'Office Supplies', 'Furniture', 'Packaging', 'Safety', 'Other']

const EMPTY = {
  sku: '',
  name: '',
  category: 'Electronics',
  quantity: 0,
  reorder_level: 10,
  unit_price: 0,
  supplier: '',
  location: '',
}

export default function ProductModal({ product, onSave, onClose }) {
  const isEdit = Boolean(product?.id)
  const [form, setForm] = useState(() => ({ ...EMPTY, ...(isEdit ? product : {}) }))
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await onSave({
        sku: form.sku.trim().toUpperCase(),
        name: form.name.trim(),
        category: form.category,
        quantity: Number(form.quantity),
        reorder_level: Number(form.reorder_level),
        unit_price: Number(form.unit_price),
        supplier: form.supplier?.trim() || null,
        location: form.location?.trim() || null,
      })
    } catch (err) {
      setError(err.message)
      setSaving(false)
    }
  }

  return (
    <Modal title={isEdit ? `Edit ${product.name}` : 'Add product'} onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <div className="form-row">
          <label>
            SKU
            <input required minLength={2} maxLength={40} value={form.sku} onChange={set('sku')} placeholder="ELEC-1004" />
          </label>
          <label>
            Category
            <select value={form.category} onChange={set('category')}>
              {CATEGORIES.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
        </div>
        <label>
          Name
          <input required maxLength={120} value={form.name} onChange={set('name')} placeholder="Mechanical keyboard" />
        </label>
        <div className="form-row three">
          <label>
            Quantity
            <input type="number" min="0" required value={form.quantity} onChange={set('quantity')} disabled={isEdit} />
          </label>
          <label>
            Reorder at
            <input type="number" min="0" required value={form.reorder_level} onChange={set('reorder_level')} />
          </label>
          <label>
            Unit price (₹)
            <input type="number" min="0" step="0.01" required value={form.unit_price} onChange={set('unit_price')} />
          </label>
        </div>
        {isEdit && <p className="muted">Use “Adjust” on the product row to change stock so the movement is recorded.</p>}
        <div className="form-row">
          <label>
            Supplier
            <input maxLength={120} value={form.supplier ?? ''} onChange={set('supplier')} />
          </label>
          <label>
            Location
            <input maxLength={60} value={form.location ?? ''} onChange={set('location')} placeholder="A1-05" />
          </label>
        </div>
        {error && <p className="form-error">{error}</p>}
        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving…' : isEdit ? 'Save changes' : 'Add product'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
