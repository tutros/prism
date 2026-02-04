import type { ComparisonResult } from '../comparison/types'
import { WeightsPanel } from '../weights/WeightsPanel'
import { useWeightedScores } from '../weights/useWeightedScores'

interface ResultsDisplayProps {
  result: ComparisonResult
}

export function ResultsDisplay({ result }: ResultsDisplayProps) {
  const { weights, scores, updateWeight } = useWeightedScores(result.criteria)

  if (result.status === 'processing') {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        <span className="ml-3 text-gray-600">Analyzing options...</span>
      </div>
    )
  }

  if (result.status === 'error') {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-700">An error occurred during analysis.</p>
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
          <div key={criterion.id} className="p-4 bg-white border border-gray-200 rounded-lg">
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
