import { useMemo, useState } from 'react'
import AnalysisConsole from '../components/AnalysisConsole'
import Analytics from '../components/Analytics'
import FindingCard from '../components/FindingCard'
import { api } from '../services/api'
import { getAnalytics, getSeverityOrder, normalizeSeverity } from '../utils/analytics'

const severityFilters = [['all', 'All'], ['priority', 'Critical / high'], ['medium', 'Medium'], ['low', 'Low / info']]

function matchesSeverity(finding, filter) {
  const severity = normalizeSeverity(finding.severity)
  if (filter === 'all') return true
  if (filter === 'priority') return ['critical', 'high'].includes(severity)
  if (filter === 'low') return ['low', 'info', 'informational'].includes(severity)
  return severity === filter
}

export default function HomePage() {
  const [mode, setMode] = useState('url')
  const [loading, setLoading] = useState(false)
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [severityFilter, setSeverityFilter] = useState('all')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [sortBy, setSortBy] = useState('severity')

  const findings = useMemo(() => result?.findings || [], [result])
  const categories = useMemo(() => [...new Set(findings.map((finding) => finding.category).filter(Boolean))].sort(), [findings])
  const sources = useMemo(() => [...new Set(findings.flatMap((finding) => finding.sources || []))].sort(), [findings])
  const analytics = useMemo(() => getAnalytics(findings, result?.summary?.severity_counts), [findings, result])
  const filteredFindings = useMemo(() => {
    const filtered = findings.filter((finding) => matchesSeverity(finding, severityFilter)
      && (categoryFilter === 'all' || finding.category === categoryFilter)
      && (sourceFilter === 'all' || finding.sources?.includes(sourceFilter)))
    return [...filtered].sort((first, second) => {
      if (sortBy === 'category') return String(first.category || '').localeCompare(String(second.category || ''))
      if (sortBy === 'confidence') return (typeof second.confidence === 'number' ? second.confidence : -1) - (typeof first.confidence === 'number' ? first.confidence : -1)
      return getSeverityOrder(first.severity) - getSeverityOrder(second.severity)
    })
  }, [findings, severityFilter, categoryFilter, sourceFilter, sortBy])

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (loading) return
    const websiteUrl = url.trim()
    if (!websiteUrl) return setError('Enter a website URL to begin inspection.')
    try {
      const parsedUrl = new URL(websiteUrl)
      if (!['http:', 'https:'].includes(parsedUrl.protocol)) return setError('Enter a valid HTTP or HTTPS URL.')
      setLoading(true); setError(''); setResult(null)
      const response = await api.post('/analyze', { url: websiteUrl })
      setResult(response.data)
    } catch (requestError) {
      const message = requestError.response?.data?.detail?.[0]?.msg || requestError.response?.data?.detail || requestError.message
      setError(typeof message === 'string' ? message : 'Unable to analyze this website.')
    } finally { setLoading(false) }
  }

  const clearFilters = () => { setSeverityFilter('all'); setCategoryFilter('all'); setSourceFilter('all') }
  const resetInspection = () => { setResult(null); setError(''); clearFilters(); setSortBy('severity') }
  const hasConfidence = findings.some((finding) => typeof finding.confidence === 'number')

  return <main className="workspace">
    <nav className="topbar" aria-label="Primary navigation"><a className="brand" href="#top" aria-label="Preflight home"><span className="brand-mark" aria-hidden="true">⌁</span><span>PRE<span>FLIGHT</span></span></a><span className="product-label">WEBSITE INTELLIGENCE</span><span className="system-indicator"><i />LOCAL API</span></nav>
    <section className="intro" id="top"><p className="eyebrow">ANALYZE · IMPROVE · SHIP</p><h1>Your website.<br /><em>Under inspection.</em></h1><p className="intro-copy">Preflight combines crawler evidence, deterministic HCI checks, visual analysis, and an AI critic to surface concrete website improvements.</p><p className="metadata">CRAWLER <b>·</b> HCI RULES <b>·</b> VISUAL ANALYSIS <b>·</b> AI CRITIC</p></section>
    <section className="inspection-panel" aria-labelledby="inspect-title"><div className="mode-switch" role="tablist" aria-label="Inspection source"><button className={mode === 'url' ? 'active' : ''} type="button" role="tab" aria-selected={mode === 'url'} onClick={() => setMode('url')}>URL</button><button className={mode === 'screenshot' ? 'active' : ''} type="button" role="tab" aria-selected={mode === 'screenshot'} onClick={() => setMode('screenshot')}>SCREENSHOT</button></div>{mode === 'url' ? <form onSubmit={handleSubmit} noValidate><label htmlFor="website-url" id="inspect-title">TARGET URL</label><div className="url-row"><span className="url-icon" aria-hidden="true">↗</span><input id="website-url" type="url" value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://example.com" disabled={loading} /><button className="inspect-button" disabled={loading} type="submit">{loading ? 'Inspecting' : 'Inspect website'}<span aria-hidden="true">→</span></button></div></form> : <div className="upload-placeholder"><label htmlFor="website-screenshot">SCREENSHOT FILE</label><input id="website-screenshot" type="file" accept="image/*" disabled /><p>Screenshot upload is not connected to an analysis endpoint yet.</p></div>}{error && <p className="inline-error" role="alert">{error}</p>}</section>
    <AnalysisConsole loading={loading} result={result} />
    {result && <section className="report" aria-labelledby="report-title"><div className="report-heading"><div><p className="eyebrow">FINAL REPORT</p><h2 id="report-title">Issues that need attention</h2><p className="report-url">{result.url || url}</p></div><button type="button" className="secondary-button" onClick={resetInspection}>Analyze another site</button></div><div className="report-summary"><div><span>FINDINGS</span><strong>{result.summary?.total_findings ?? findings.length}</strong></div><div><span>STATUS</span><strong>{result.analysis_status?.status || 'completed'}</strong></div>{Object.entries(result.summary?.severity_counts || {}).filter(([, count]) => count > 0).map(([severity, count]) => <div key={severity} className={`summary-${normalizeSeverity(severity)}`}><span>{severity}</span><strong>{count}</strong></div>)}</div>{result.analysis_status?.status === 'partial' && <p className="partial-note">Some optional analysis components did not complete. Available findings are shown below.</p>}<Analytics analytics={analytics} /><div className="filter-bar" aria-label="Finding filters"><div className="filter-group">{severityFilters.map(([value, label]) => <button key={value} type="button" className={severityFilter === value ? 'selected' : ''} onClick={() => setSeverityFilter(value)}>{label}</button>)}</div><label>Category<select value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value)}><option value="all">All categories</option>{categories.map((category) => <option key={category} value={category}>{category}</option>)}</select></label>{sources.length > 0 && <label>Source<select value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)}><option value="all">All sources</option>{sources.map((source) => <option key={source} value={source}>{source}</option>)}</select></label>}<label>Sort<select value={sortBy} onChange={(event) => setSortBy(event.target.value)}><option value="severity">Severity</option><option value="category">Category</option>{hasConfidence && <option value="confidence">Confidence</option>}</select></label></div>{findings.length === 0 ? <div className="empty-state"><span>✓</span><h3>No issues were identified by the completed checks.</h3><p>Automated analysis cannot guarantee a defect-free website; review critical user journeys manually.</p></div> : filteredFindings.length === 0 ? <div className="empty-state"><h3>No findings match these filters.</h3><button type="button" onClick={clearFilters}>Clear filters</button></div> : <div className="finding-list">{filteredFindings.map((finding, index) => <FindingCard key={`${finding.id || 'finding'}-${index}`} finding={finding} />)}</div>}</section>}
  </main>
}
