import { normalizeSeverity } from '../utils/analytics'

function Detail({ label, value, accent = false }) {
  return (
    <div className={`finding-detail ${accent ? 'recommendation' : ''}`}>
      <span>{label}</span>
      <p>{value}</p>
    </div>
  )
}

export default function FindingCard({ finding }) {
  const severity = normalizeSeverity(finding.severity)
  const confidence = typeof finding.confidence === 'number' ? `${Math.round(finding.confidence * 100)}% confidence` : null

  return (
    <article className={`finding severity-${severity}`}>
      <header className="finding-header">
        <span className="severity-badge">{severity}</span>
        {finding.category && <span className="finding-category">{finding.category}</span>}
        {finding.id && <span className="finding-id">{finding.id}</span>}
      </header>
      <h3>{finding.problem || 'Reported usability issue'}</h3>
      {finding.element && <p className="element-label">ELEMENT · {finding.element}</p>}
      {finding.user_impact && <Detail label="Why it matters" value={finding.user_impact} />}
      {finding.evidence && <Detail label="Evidence" value={finding.evidence} />}
      {finding.recommendation && <Detail label="Recommendation" value={finding.recommendation} accent />}
      {(confidence || finding.sources?.length > 0) && <footer className="finding-footer">
        {confidence && <span>{confidence}</span>}
        {finding.sources?.length > 0 && <span>Sources · {finding.sources.join(', ')}</span>}
      </footer>}
    </article>
  )
}
