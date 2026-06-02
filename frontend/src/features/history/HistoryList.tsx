import { useHistory } from './useHistory'
import { apiGet } from '../../lib/api'
import type { AnalysisResult } from '../../lib/api'
import { useQueries } from '@tanstack/react-query'

interface Props {
  activeDecisionId: string | null
  onSelect: (decisionId: string, analysisId: string) => void
}

const TIER_STYLE: Record<string, { bg: string; color: string }> = {
  quick:  { bg: '#fff4e0', color: '#d97706' },
  medium: { bg: '#e7f5e8', color: '#16a34a' },
  deep:   { bg: '#ede8ff', color: '#5b3df5' },
}

export function HistoryList({ activeDecisionId, onSelect }: Props) {
  const { data, isLoading } = useHistory()
  const decisions = data?.decisions ?? []

  // Fetch latest analysis for each decision to get tier + winner
  const analysisQueries = useQueries({
    queries: decisions.map(d => ({
      queryKey: ['analyses-list', d.decision_id],
      queryFn: () => apiGet<{ analyses: AnalysisResult[] }>(`/api/decisions/${d.decision_id}/analyses`),
      staleTime: 30000,
    })),
  })

  if (isLoading) return <p style={{ fontSize: 12, color: 'var(--txm)', padding: '8px 4px' }}>Loading…</p>
  if (decisions.length === 0) return <p style={{ fontSize: 12, color: 'var(--txm)', padding: '8px 4px' }}>No analyses yet.</p>

  return (
    <>
      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--txm)', letterSpacing: '0.07em', textTransform: 'uppercase', marginBottom: 14 }}>
        Past Analyses
      </div>
      {decisions.map((d, i) => {
        const analyses = analysisQueries[i]?.data?.analyses ?? []
        const latest = analyses[analyses.length - 1]
        const tier = latest?.tier ?? 'medium'
        const tierStyle = TIER_STYLE[tier] ?? TIER_STYLE.medium
        const isActive = d.decision_id === activeDecisionId

        return (
          <div
            key={d.decision_id}
            onClick={() => latest && onSelect(d.decision_id, latest.analysis_id)}
            style={{
              padding: '11px 13px', borderRadius: 12, cursor: latest ? 'pointer' : 'default',
              marginBottom: 6, border: `1px solid ${isActive ? 'var(--ac)' : 'transparent'}`,
              background: isActive ? 'var(--ac-dim)' : 'transparent', transition: 'all 0.15s',
            }}
            onMouseEnter={e => { if (!isActive) { (e.currentTarget as HTMLElement).style.background = 'var(--sf2)'; (e.currentTarget as HTMLElement).style.borderColor = 'var(--bd)' } }}
            onMouseLeave={e => { if (!isActive) { (e.currentTarget as HTMLElement).style.background = 'transparent'; (e.currentTarget as HTMLElement).style.borderColor = 'transparent' } }}
          >
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--txb)', marginBottom: 5, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {d.title}
            </div>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap', marginBottom: 4 }}>
              <span style={{ fontSize: 10, fontWeight: 700, padding: '2px 9px', borderRadius: 20, background: tierStyle.bg, color: tierStyle.color }}>
                {tier}
              </span>
              {latest?.winner && (
                <span style={{ fontSize: 11, color: 'var(--ac)', fontWeight: 600 }}>→ {latest.winner}</span>
              )}
            </div>
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
              {d.options.slice(0, 3).map(o => (
                <span key={o} style={{ fontSize: 10, color: 'var(--txm)', background: 'var(--sf2)', padding: '1px 7px', borderRadius: 100, border: '1px solid var(--bd)' }}>{o}</span>
              ))}
              {d.options.length > 3 && (
                <span style={{ fontSize: 10, color: 'var(--txm)' }}>+{d.options.length - 3}</span>
              )}
            </div>
          </div>
        )
      })}
    </>
  )
}
