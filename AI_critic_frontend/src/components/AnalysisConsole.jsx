const PIPELINE = [
  ['crawler', 'CRAWLER', 'Collecting page structure and evidence'],
  ['hci_rules', 'HCI RULES', 'Evaluating deterministic usability checks'],
  ['vlm', 'VISUAL ANALYSIS', 'Reviewing screenshot evidence'],
  ['critic', 'AI CRITIC', 'Identifying additional supported issues'],
  ['report', 'REPORT ENGINE', 'Merging and prioritizing findings'],
]

function statusFor(stage, result, loading) {
  if (loading) return { label: 'AWAITING CONFIRMATION', type: 'pending' }
  if (!result) return { label: 'STANDBY', type: 'pending' }
  if (stage === 'report') {
    return result.analysis_status?.status === 'completed'
      ? { label: 'COMPLETE', type: 'complete' }
      : { label: 'PARTIAL', type: 'partial' }
  }

  const component = result.analysis_status?.components?.[stage]
  if (component?.status === 'completed') return { label: 'COMPLETE', type: 'complete' }
  if (component?.status === 'unavailable') return { label: 'UNAVAILABLE', type: 'partial' }
  if (component?.status === 'failed') return { label: 'FAILED', type: 'failed' }
  return { label: 'NOT REPORTED', type: 'pending' }
}

export default function AnalysisConsole({ loading, result }) {
  const completed = result?.analysis_status?.status === 'completed'
  const partial = result?.analysis_status?.status === 'partial'

  return (
    <section className={`console ${loading ? 'is-running' : ''}`} aria-live="polite">
      <div className="console-scan" aria-hidden="true" />
      <div className="console-header">
        <div>
          <p className="eyebrow">INSPECTION CONSOLE</p>
          <h2>{loading ? 'Analysis in progress' : completed ? 'Inspection complete' : partial ? 'Inspection completed with limitations' : 'Ready for inspection'}</h2>
        </div>
        <span className={`overall-status ${loading ? 'running' : partial ? 'partial' : completed ? 'complete' : 'idle'}`}>
          <span aria-hidden="true" />
          {loading ? 'REQUEST IN FLIGHT' : partial ? 'PARTIAL' : completed ? 'COMPLETE' : 'STANDBY'}
        </span>
      </div>
      {loading && <p className="console-note">Preflight is waiting for confirmed crawl and analysis results. Progress is indeterminate until the response arrives.</p>}
      <ol className="pipeline">
        {PIPELINE.map(([key, label, description], index) => {
          const status = statusFor(key, result, loading)
          return (
            <li className={`pipeline-item ${status.type}`} key={key}>
              <span className="pipeline-number">{String(index + 1).padStart(2, '0')}</span>
              <span className="pipeline-mark" aria-hidden="true">{status.type === 'complete' ? '✓' : '·'}</span>
              <span className="pipeline-copy"><strong>{label}</strong><small>{description}</small></span>
              <span className="pipeline-status">{status.label}</span>
            </li>
          )
        })}
      </ol>
    </section>
  )
}
