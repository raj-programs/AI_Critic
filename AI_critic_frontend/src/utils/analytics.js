const SEVERITY_ORDER = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
  informational: 4,
}

export function normalizeSeverity(severity) {
  return String(severity || 'info').toLowerCase()
}

export function getSeverityOrder(severity) {
  return SEVERITY_ORDER[normalizeSeverity(severity)] ?? 5
}

export function countBy(findings, getKey) {
  return findings.reduce((counts, finding) => {
    const key = getKey(finding)
    if (key) counts[key] = (counts[key] || 0) + 1
    return counts
  }, {})
}

export function toChartItems(counts, preferredOrder = []) {
  const items = Object.entries(counts).map(([label, value]) => ({ label, value }))
  return items.sort((first, second) => {
    const firstIndex = preferredOrder.indexOf(first.label)
    const secondIndex = preferredOrder.indexOf(second.label)
    if (firstIndex !== -1 || secondIndex !== -1) {
      return (firstIndex === -1 ? Infinity : firstIndex) - (secondIndex === -1 ? Infinity : secondIndex)
    }
    return second.value - first.value || first.label.localeCompare(second.label)
  })
}

export function getAnalytics(findings, reportedSeverityCounts) {
  const severityCounts = reportedSeverityCounts || countBy(findings, (finding) => normalizeSeverity(finding.severity))
  const categoryCounts = countBy(findings, (finding) => finding.category)
  const sourceCounts = findings.reduce((counts, finding) => {
    (finding.sources || []).forEach((source) => {
      counts[source] = (counts[source] || 0) + 1
    })
    return counts
  }, {})

  return {
    severity: toChartItems(severityCounts, ['critical', 'high', 'medium', 'low', 'info', 'informational']).filter((item) => item.value > 0),
    categories: toChartItems(categoryCounts),
    sources: toChartItems(sourceCounts),
    confidentFindings: findings.filter((finding) => typeof finding.confidence === 'number').length,
  }
}
