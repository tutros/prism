import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../../lib/api'
import type { ComparisonResult } from '../comparison/types'

export function useResults(comparisonId: string | null) {
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
      return 1000
    },
  })
}
