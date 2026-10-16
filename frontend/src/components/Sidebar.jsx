const NAV = [
  { label: 'Dashboard', icon: '▦', active: true },
  { label: 'Products', icon: '◫' },
  { label: 'Stock movements', icon: '⇅' },
  { label: 'Suppliers', icon: '⌂' },
  { label: 'Reports', icon: '◔' },
]

// Baked in at build time by CI (Docker build-arg APP_VERSION = git SHA).
const VERSION = import.meta.env.VITE_APP_VERSION || 'dev'

export default function Sidebar({ open, onClose, lowStock }) {
  return (
    <>
      <div className={`scrim ${open ? 'show' : ''}`} onClick={onClose} aria-hidden="true" />
      <nav className={`sidebar ${open ? 'open' : ''}`} aria-label="Main navigation">
        <div className="brand">
          <span className="logo" aria-hidden="true">
            ◈
          </span>
          <div>
            <strong>StockPilot</strong>
            <small>Inventory control</small>
          </div>
        </div>

        <p className="nav-label">Workspace</p>
        <ul className="nav">
          {NAV.map((item) => (
            <li key={item.label}>
              <a href="#" className={item.active ? 'active' : ''} onClick={(e) => e.preventDefault()}>
                <span aria-hidden="true">{item.icon}</span>
                {item.label}
                {item.label === 'Products' && lowStock > 0 && <span className="pill">{lowStock} low</span>}
              </a>
            </li>
          ))}
        </ul>

        <div className="pipeline">
          <p className="nav-label">Deployment</p>
          <div className="pipeline-row">
            <span className="dot ok" /> CI/CD · GitHub Actions
          </div>
          <div className="pipeline-row">
            <span className="dot ok" /> GitOps · Argo CD
          </div>
          <code title="Image tag (git commit SHA)">build {VERSION.slice(0, 7)}</code>
        </div>
      </nav>
    </>
  )
}
