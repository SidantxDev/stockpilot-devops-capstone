import { timeAgo } from '../api.js'

export default function ActivityFeed({ movements }) {
  return (
    <section className="card">
      <div className="card-head">
        <h2>Recent stock movements</h2>
      </div>
      {movements.length === 0 ? (
        <p className="muted pad">No movements yet. Use “Adjust” on a product to record one.</p>
      ) : (
        <ul className="feed">
          {movements.map((m) => (
            <li key={m.id}>
              <span className={`delta ${m.change > 0 ? 'in' : 'out'}`}>
                {m.change > 0 ? '+' : ''}
                {m.change}
              </span>
              <div>
                <strong>{m.product_name}</strong>
                <small>
                  {m.reason}
                  {m.note ? ` · ${m.note}` : ''} · {timeAgo(m.created_at)}
                </small>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
