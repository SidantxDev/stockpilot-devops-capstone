// All calls are same-origin (`/api/...`). Nginx (Docker Compose) or the
// Kubernetes Ingress routes them to the FastAPI backend.
const BASE = '/api'

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') detail = body.detail
      else if (Array.isArray(body.detail)) detail = body.detail.map((d) => `${d.loc?.at(-1)}: ${d.msg}`).join(', ')
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail)
  }
  return response.status === 204 ? null : response.json()
}

export const api = {
  listProducts: (params = {}) => {
    const query = new URLSearchParams(Object.entries(params).filter(([, v]) => v))
    return request(`/products${query.size ? `?${query}` : ''}`)
  },
  stats: () => request('/products/stats'),
  movements: (limit = 8) => request(`/movements?limit=${limit}`),
  createProduct: (data) => request('/products', { method: 'POST', body: JSON.stringify(data) }),
  updateProduct: (id, data) => request(`/products/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteProduct: (id) => request(`/products/${id}`, { method: 'DELETE' }),
  adjustStock: (id, data) => request(`/products/${id}/adjust`, { method: 'POST', body: JSON.stringify(data) }),
}

export const formatINR = (value) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value ?? 0)

export const timeAgo = (iso) => {
  const seconds = Math.max(1, Math.round((Date.now() - new Date(iso).getTime()) / 1000))
  if (seconds < 60) return `${seconds}s ago`
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.round(seconds / 3600)}h ago`
  return `${Math.round(seconds / 86400)}d ago`
}
