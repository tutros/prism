import { useMutation } from '@tanstack/react-query'
import { apiPost } from '../../lib/api'
import type { ComparisonInput, SubmitResponse } from './types'

export function useComparison() {
  return useMutation({
    mutationFn: async (data: ComparisonInput) => {
      return apiPost<SubmitResponse>('/api/compare', data)
    },
  })
}
