import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiPost } from '../../lib/api'
import type { ComparisonResult } from '../comparison/types'

interface RegenerateWeightsProps {
  comparisonId: string
}

export function RegenerateWeights({ comparisonId }: RegenerateWeightsProps) {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: async () => {
      // apiPost already returns parsed JSON and throws on error
      return apiPost<ComparisonResult>(`/api/comparisons/${comparisonId}/regenerate-weights`, {})
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['results', comparisonId] })
    },
  })

  return (
    <button
      onClick={() => mutation.mutate()}
      disabled={mutation.isPending}
      className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
    >
      {mutation.isPending ? (
        <>
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          Regenerating...
        </>
      ) : (
        'Regenerate Weights'
      )}
    </button>
  )
}
