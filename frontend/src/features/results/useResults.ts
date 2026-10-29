import { useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../../lib/api'
import type { AnalysisResult } from '../../lib/api'

const POLL_TIMEOUT_MS = 120_000

export function useResults(analysisId: string | null, decisionId?: string | null) {
  // Set on the first poll decision, not during render (react-hooks/purity).
  const startTimeRef = useRef<number | null>(null)
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
      const startedAt = (startTimeRef.current ??= Date.now())
      if (Date.now() - startedAt > POLL_TIMEOUT_MS) return false
      return 1500
    },
    retry: 1,
  })
}
