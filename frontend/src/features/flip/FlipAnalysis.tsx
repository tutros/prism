import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../../lib/api'
import type { FlipAnalysisResponse } from '../comparison/types'

interface FlipAnalysisProps {
  comparisonId: string
  loserName: string
}

export function FlipAnalysis({ comparisonId, loserName }: FlipAnalysisProps) {

  const { data, isLoading, error } = useQuery({
    queryKey: ['flip-analysis', comparisonId],
    queryFn: async () => {
      // apiGet already returns parsed JSON and throws on error
      return apiGet<FlipAnalysisResponse>(`/api/comparisons/${comparisonId}/flip-analysis`)
    },
    staleTime: 60000, // Cache for 1 minute
    placeholderData: (previousData) => previousData, // Keep previous data during refetch to prevent flickering
  })

  if (isLoading && !data) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center gap-2 text-gray-600">
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
          Analyzing what would flip the outcome...
        </div>
      </div>
    )
  }

  if (error || !data) {
    return null
  }

  if (data.suggestions.length === 0) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg text-gray-600">
        <p className="font-medium">No realistic way to flip this outcome</p>
        <p className="text-sm mt-1">The winner outperforms on most criteria, or the gap is too large to overcome with weight adjustments alone.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h3 className="font-semibold text-lg text-gray-800">
        What would make {loserName} win?
      </h3>
      {data.suggestions.map((suggestion) => (
        <div
          key={suggestion.affected_criterion}
          className="p-4 bg-amber-50 border border-amber-200 rounded-lg"
        >
          <p className="font-medium text-amber-900">{suggestion.action}</p>
          <p className="text-sm text-amber-700 mt-1">{suggestion.impact}</p>
          <p className="text-xs text-amber-600 mt-1">
            Affects: {suggestion.affected_criterion}
          </p>
          {suggestion.sources.length > 0 && (
            <div className="mt-2 text-xs text-amber-600">
              Sources:{' '}
              {suggestion.sources.map((src, j) => (
                <a
                  key={src}
                  href={src}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline hover:text-amber-800 ml-1"
                >
                  [{j + 1}]
                </a>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
