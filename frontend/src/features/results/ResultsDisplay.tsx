import type { ComparisonResult } from '../comparison/types'
import { WeightsPanel } from '../weights/WeightsPanel'
import { useWeightedScores } from '../weights/useWeightedScores'
import { useProgress } from '../progress/useProgress'
import { ProgressDisplay } from '../progress/ProgressDisplay'

interface ResultsDisplayProps {
  result: ComparisonResult
  comparisonId: string | null
}

export function ResultsDisplay({ result, comparisonId }: ResultsDisplayProps) {
  const { weights, scores, updateWeight } = useWeightedScores(result.criteria)
  const progress = useProgress(
    result.status === 'processing' ? comparisonId : null
  )

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
          <div className="text-2xl font-bold text-gray-800">{scores.totalA}</div>
        </div>
        <div className={`p-4 rounded-lg border-2 ${scores.winner === 'b' ? 'border-green-500 bg-green-50' : 'border-gray-200 bg-white'}`}>
          <h3 className="text-lg font-bold mb-2">{result.option_b_name}</h3>
          {scores.winner === 'b' && (
            <span className="inline-block px-2 py-1 text-xs font-medium bg-green-500 text-white rounded mb-2">
              Winner
            </span>
          )}
          <div className="text-2xl font-bold text-gray-800">{scores.totalB}</div>
        </div>
      </div>

      {/* Weights Panel */}
      <WeightsPanel
        criteria={result.criteria}
        weights={weights}
        scores={scores}
        optionAName={result.option_a_name}
        optionBName={result.option_b_name}
        onWeightChange={updateWeight}
      />

      {/* Criteria Details */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Criteria Details</h3>
        {result.criteria.map((criterion) => (
          <div key={criterion.id} id={`criterion-${criterion.id}`} className="p-4 bg-white border border-gray-200 rounded-lg scroll-mt-4">
            <div className="flex justify-between items-start mb-2">
              <div>
                <h4 className="font-medium">{criterion.name}</h4>
                <p className="text-sm text-gray-600">{criterion.description}</p>
              </div>
              <span className="text-sm text-blue-600 font-medium">
                Weight: {weights[criterion.id] ?? criterion.weight}%
              </span>
            </div>
            <div className="grid grid-cols-2 gap-4 mt-3">
              <div>
                <span className="text-sm text-gray-500">{result.option_a_name}</span>
                <div className="text-lg font-semibold">{criterion.score_a}</div>
              </div>
              <div>
                <span className="text-sm text-gray-500">{result.option_b_name}</span>
                <div className="text-lg font-semibold">{criterion.score_b}</div>
              </div>
            </div>
            {criterion.sources.length > 0 && (
              <div className="mt-2 pt-2 border-t border-gray-100">
                <span className="text-xs text-gray-500">Sources: </span>
                {criterion.sources.map((src, i) => (
                  <a
                    key={i}
                    href={src}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:underline ml-1"
                  >
                    [{i + 1}]
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
