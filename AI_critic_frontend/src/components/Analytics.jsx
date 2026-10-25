function DistributionChart({ title, description, data, variant = 'neutral' }) {
  if (!data.length) return null
  const maxValue = Math.max(...data.map((item) => item.value))

  return (
    <section className="chart-card" aria-label={`${title}: ${data.map((item) => `${item.label} ${item.value}`).join(', ')}`}>
      <header><h3>{title}</h3><p>{description}</p></header>
      <div className="chart-bars">
        {data.map((item) => <div className={`chart-row ${variant === 'severity' ? `chart-${item.label.toLowerCase()}` : ''}`} key={item.label}>
          <span title={item.label}>{item.label}</span>
          <div className="chart-track"><i style={{ width: `${(item.value / maxValue) * 100}%` }} /></div>
          <b>{item.value}</b>
        </div>)}
      </div>
    </section>
  )
}

export default function Analytics({ analytics }) {
  const hasCharts = analytics.severity.length || analytics.categories.length || analytics.sources.length
  if (!hasCharts) return null

  return (
    <section className="analytics" aria-labelledby="analytics-title">
      <div className="section-heading"><div><p className="eyebrow">OBSERVABILITY</p><h2 id="analytics-title">Finding distribution</h2></div><p>Computed locally from returned findings. No quality score or inferred metrics.</p></div>
      <div className="chart-grid">
        <DistributionChart title="By severity" description="Prioritization at a glance" data={analytics.severity} variant="severity" />
        <DistributionChart title="By category" description="Reported issue categories" data={analytics.categories} />
        <DistributionChart title="By source" description="Contributing analysis sources" data={analytics.sources} />
      </div>
    </section>
  )
}
