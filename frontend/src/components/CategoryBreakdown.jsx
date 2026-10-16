export default function CategoryBreakdown({ categories }) {
  const entries = Object.entries(categories ?? {}).sort((a, b) => b[1] - a[1])
  const max = Math.max(1, ...entries.map(([, n]) => n))

  return (
    <section className="card">
      <div className="card-head">
        <h2>Products by category</h2>
      </div>
      {entries.length === 0 ? (
        <p className="muted pad">No categories yet.</p>
      ) : (
        <ul className="bars">
          {entries.map(([name, count]) => (
            <li key={name}>
              <span className="bar-label">{name}</span>
              <span className="bar-track">
                <span className="bar-fill" style={{ width: `${(count / max) * 100}%` }} />
              </span>
              <span className="bar-value">{count}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
