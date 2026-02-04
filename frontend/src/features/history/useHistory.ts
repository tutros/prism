import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../../lib/api'

interface ComparisonSummary {
  comparison_id: string
  option_a_name: string
  option_b_name: string
  status: 'processing' | 'completed' | 'error'
  created_at: string | null
}

interface HistoryResponse {
  comparisons: ComparisonSummary[]
}

export function useHistory() {
  return useQuery({
    queryKey: ['history'],
    queryFn: () => apiGet<HistoryResponse>('/api/results'),
    staleTime: 30000, // 30 seconds
  })
}

export type { ComparisonSummary }
