import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../../lib/api'
import type { ComparisonResult } from '../comparison/types'

const POLL_TIMEOUT_MS = 120_000 // Stop polling after 2 minutes

export function useResults(comparisonId: string | null) {
  const pollStartRef = { current: Date.now() }

  return useQuery({
    queryKey: ['comparison', comparisonId],
    queryFn: async () => {
      if (!comparisonId) throw new Error('No comparison ID')
      return apiGet<ComparisonResult>(`/api/results/${comparisonId}`)
    },
    enabled: !!comparisonId,
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data || data.status === 'completed' || data.status === 'error') {
        return false
      }
      // Stop polling if stuck in processing too long
      if (Date.now() - pollStartRef.current > POLL_TIMEOUT_MS) {
        return false
      }
      return 1000
    },
    retry: 1, // Reduce retries to avoid 14s freeze during 1s polling
  })
}
