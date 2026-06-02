import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../../lib/api'
import type { DecisionSummary } from '../../lib/api'

interface HistoryResponse {
  decisions: DecisionSummary[]
}

export function useHistory() {
  return useQuery({
    queryKey: ['decisions'],
    queryFn: () => apiGet<HistoryResponse>('/api/decisions'),
    staleTime: 30000,
  })
}
