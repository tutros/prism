import { useQuery } from '@tanstack/react-query'
import type { ComparisonResult, FlipAnalysisResponse } from '../comparison/types'
import { WeightsPanel } from '../weights/WeightsPanel'
import { useWeightedScores } from '../weights/useWeightedScores'
import { useProgress } from '../progress/useProgress'
import { ProgressDisplay } from '../progress/ProgressDisplay'
import { ScoringExplainer } from './ScoringExplainer'
import { GoDeeper } from '../criteria/GoDeeper'
import { RegenerateWeights } from '../weights/RegenerateWeights'
import { FlipAnalysis } from '../flip/FlipAnalysis'
import { CriteriaEditor } from '../criteria/CriteriaEditor'
import { AddCriterion } from '../criteria/AddCriterion'
import { apiGet, apiPost } from '../../lib/api'

function formatCacheAge(cachedAt: string): string {
  const cached = new Date(cachedAt)
  const now = new Date()
  const diffMs = now.getTime() - cached.getTime()
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffMinutes = Math.floor(diffMs / (1000 * 60))

  if (diffHours >= 1) {
    return `${diffHours}h ago`
  }
  return `${diffMinutes}m ago`
}

interface ResultsDisplayProps {
  result: ComparisonResult
  comparisonId: string | null
  onNewComparison?: (id: string) => void
}

export function ResultsDisplay({ result, comparisonId, onNewComparison }: ResultsDisplayProps) {
  const { weights, scores, updateWeight } = useWeightedScores(result.criteria)
  const progress = useProgress(
    result.status === 'processing' ? comparisonId : null
  )

  // Fetch sensitivity data for criteria (shares query key with FlipAnalysis component)
  const { data: flipData } = useQuery({
    queryKey: ['flip-analysis', comparisonId],
    queryFn: async () => {
      return apiGet<FlipAnalysisResponse>(`/api/comparisons/${comparisonId}/flip-analysis`)
    },
    enabled: !!comparisonId && result.status === 'completed',
    staleTime: 60000, // Must match FlipAnalysis staleTime to avoid cache fights
  })

  if (result.status === 'processing') {
    return (
      <ProgressDisplay
        status={progress.status}
        connected={progress.connected}
      />
    )
  }

  if (result.status === 'error') {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-700 font-medium">An error occurred during analysis.</p>
        {result.reasoning && (
          <p className="text-red-600 text-sm mt-2">{result.reasoning}</p>
        )}
      </div>
    )
  }

  // Use calculated winner instead of server's winner
  const winnerLabel = scores.winner === 'a'
    ? result.option_a_name
    : scores.winner === 'b'
    ? result.option_b_name
    : 'Tie'

  const loserLabel = scores.winner === 'a'
    ? result.option_b_name
    : scores.winner === 'b'
    ? result.option_a_name
    : null

  return (
    <div className="space-y-6">
      {/* Winner Banner */}
      <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
        <p className="text-lg font-semibold text-green-800">
          Winner: {winnerLabel}
        </p>
        <p className="text-sm text-green-700 mt-1">{result.reasoning}</p>
      </div>

      {/* Cache Age Indicator */}
      {result.tavily_cached_at && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-center justify-between">
          <p className="text-sm text-amber-700">
            Results based on cached research data ({formatCacheAge(result.tavily_cached_at)})
          </p>
          <button
            onClick={() => {
              if (comparisonId && onNewComparison) {
                const params = new URLSearchParams({ force_refresh: 'true' })
                apiPost<{ comparison_id: string }>(`/api/compare?${params}`, {
                  option_a: result.option_a_name,
                  option_b: result.option_b_name,
                  intent: result.intent,
                }).then(data => {
                  onNewComparison(data.comparison_id)
                }).catch(() => {
                  // Error is visible in browser console; button remains clickable for retry
                })
              }
            }}
            className="px-3 py-1 text-sm font-medium text-amber-700 bg-amber-100 hover:bg-amber-200 rounded border border-amber-300 transition-colors"
          >
            Refresh with latest data
          </button>
        </div>
      )}

      {/* Side-by-side Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className={`p-4 rounded-lg border-2 ${scores.winner === 'a' ? 'border-green-500 bg-green-50' : 'border-gray-200 bg-white'}`}>
          <h3 className="text-lg font-bold mb-2">{result.option_a_name}</h3>
          {scores.winner === 'a' && (
            <span className="inline-block px-2 py-1 text-xs font-medium bg-green-500 text-white rounded mb-2">
              Winner
            </span>
          )}
          <div className="text-2xl font-bold text-gray-800">{scores.totalA}<span className="text-sm font-normal text-gray-500">/100</span></div>
        </div>
        <div className={`p-4 rounded-lg border-2 ${scores.winner === 'b' ? 'border-green-500 bg-green-50' : 'border-gray-200 bg-white'}`}>
          <h3 className="text-lg font-bold mb-2">{result.option_b_name}</h3>
          {scores.winner === 'b' && (
            <span className="inline-block px-2 py-1 text-xs font-medium bg-green-500 text-white rounded mb-2">
              Winner
            </span>
          )}
          <div className="text-2xl font-bold text-gray-800">{scores.totalB}<span className="text-sm font-normal text-gray-500">/100</span></div>
        </div>
      </div>

      {/* Flip Analysis */}
      {comparisonId && loserLabel && scores.winner !== 'tie' && (
        <FlipAnalysis
          comparisonId={comparisonId}
          loserName={loserLabel}
        />
      )}

      {/* Scoring Explanation */}
      <ScoringExplainer />

      {/* Weights Panel */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Weights</h3>
          {comparisonId && <RegenerateWeights comparisonId={comparisonId} />}
        </div>
        <WeightsPanel
          criteria={result.criteria}
          weights={weights}
          scores={scores}
          optionAName={result.option_a_name}
          optionBName={result.option_b_name}
          onWeightChange={updateWeight}
        />
      </div>

      {/* Criteria Details */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Criteria Details</h3>
          {comparisonId && <GoDeeper comparisonId={comparisonId} />}
        </div>
        {result.criteria.map((criterion) => (
          <CriteriaEditor
            key={criterion.id}
            criterion={criterion}
            comparisonId={comparisonId || ''}
            optionAName={result.option_a_name}
            optionBName={result.option_b_name}
            weight={weights[criterion.id] ?? criterion.weight}
            sensitivity={flipData?.sensitivity[criterion.id] ?? 0.5}
            sourceMetadata={result.source_metadata ?? {}}
          />
        ))}
        {comparisonId && (
          <AddCriterion
            comparisonId={comparisonId}
            optionAName={result.option_a_name}
            optionBName={result.option_b_name}
          />
        )}
      </div>
    </div>
  )
}
