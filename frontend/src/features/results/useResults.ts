import { useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../../lib/api'
import type { AnalysisResult } from '../../lib/api'

const POLL_TIMEOUT_MS = 120_000

export function useResults(analysisId: string | null, decisionId?: string | null) {
  // Poll-timeout start, per analysis. Set on the first poll decision, not
  // during render (react-hooks/purity); re-keyed when analysisId changes so a
  // long-lived ResultsDisplay does not carry an old start time to a new analysis.
  const startRef = useRef<{ id: string | null; startedAt: number } | null>(null)
  return useQuery({
    queryKey: ['analysis', decisionId, analysisId],
    queryFn: () => {
      if (!analysisId || !decisionId) throw new Error('Missing IDs')
      return apiGet<AnalysisResult>(`/api/decisions/${decisionId}/analyses/${analysisId}`)
    },
    enabled: !!analysisId && !!decisionId,
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data || data.status === 'completed' || data.status === 'error') return false
      let start = startRef.current
      if (start?.id !== analysisId) {
        start = { id: analysisId, startedAt: Date.now() }
        startRef.current = start
      }
      if (Date.now() - start.startedAt > POLL_TIMEOUT_MS) return false
      return 1500
    },
    retry: 1,
  })
}
