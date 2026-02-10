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
import { apiGet } from '../../lib/api'

interface ResultsDisplayProps {
  result: ComparisonResult
  comparisonId: string | null
}

export function ResultsDisplay({ result, comparisonId }: ResultsDisplayProps) {
  const { weights, scores, updateWeight } = useWeightedScores(result.criteria)
  const progress = useProgress(
    result.status === 'processing' ? comparisonId : null
  )

  // Fetch sensitivity data for criteria
  const { data: flipData } = useQuery({
    queryKey: ['flip-analysis', comparisonId],
    queryFn: async () => {
      // apiGet already returns parsed JSON and throws on error
      return apiGet<FlipAnalysisResponse>(`/api/comparisons/${comparisonId}/flip-analysis`)
    },
    enabled: !!comparisonId && result.status === 'completed',
    staleTime: 30000,
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
