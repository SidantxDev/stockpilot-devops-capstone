import { useState } from 'react'
import Modal from './Modal.jsx'

const REASONS = [
  { value: 'restock', label: 'Restock', direction: 1 },
  { value: 'return', label: 'Customer return', direction: 1 },
  { value: 'sale', label: 'Sale / dispatch', direction: -1 },
  { value: 'damaged', label: 'Damaged / write-off', direction: -1 },
  { value: 'correction', label: 'Stock-take correction', direction: 0 },
]

export default function AdjustModal({ product, onSave, onClose }) {
  const [reason, setReason] = useState('restock')
  const [amount, setAmount] = useState(1)
  const [note, setNote] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const direction = REASONS.find((r) => r.value === reason).direction
  // Corrections accept a signed number; other reasons imply the sign.
  const change = direction === 0 ? Number(amount) : direction * Math.abs(Number(amount))
  const after = product.quantity + change

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await onSave({ change, reason, note: note.trim() || null })
    } catch (err) {
      setError(err.message)
      setSaving(false)
    }
  }

  return (
    <Modal title={`Adjust stock · ${product.name}`} onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <label>
          Reason
          <select value={reason} onChange={(e) => setReason(e.target.value)}>
            {REASONS.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          {direction === 0 ? 'Change (use a negative number to remove)' : 'Units'}
          <input type="number" required value={amount} min={direction === 0 ? undefined : 1} onChange={(e) => setAmount(e.target.value)} />
        </label>
        <label>
          Note
          <input maxLength={200} value={note} onChange={(e) => setNote(e.target.value)} placeholder="PO-2291, order #1042…" />
        </label>
        <p className={`preview ${after < 0 ? 'bad' : ''}`}>
          {product.quantity} → <strong>{after}</strong> units
        </p>
        {error && <p className="form-error">{error}</p>}
        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn-primary" disabled={saving || change === 0 || after < 0}>
            {saving ? 'Saving…' : 'Record movement'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
