import { WeightSlider } from './WeightSlider'
import type { Criterion } from '../comparison/types'
import type { WeightedScores } from './useWeightedScores'

interface WeightsPanelProps {
  criteria: Criterion[]
  weights: Record<string, number>
  scores: WeightedScores
  optionAName: string
  optionBName: string
  onWeightChange: (criterionId: string, value: number) => void
}

export function WeightsPanel({
  criteria,
  weights,
  scores,
  optionAName,
  optionBName,
  onWeightChange,
}: WeightsPanelProps) {
  return (
    <div className="space-y-6">
      {/* Scores Summary */}
      <div className="p-4 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-medium text-gray-500 mb-3">Weighted Scores</h4>
        <div className="grid grid-cols-2 gap-4">
          <div className={`p-3 rounded-lg ${scores.winner === 'a' ? 'bg-green-100 border-2 border-green-500' : 'bg-white border border-gray-200'}`}>
            <div className="text-sm text-gray-600">{optionAName}</div>
            <div className="text-2xl font-bold">{scores.totalA}</div>
          </div>
          <div className={`p-3 rounded-lg ${scores.winner === 'b' ? 'bg-green-100 border-2 border-green-500' : 'bg-white border border-gray-200'}`}>
            <div className="text-sm text-gray-600">{optionBName}</div>
            <div className="text-2xl font-bold">{scores.totalB}</div>
          </div>
        </div>
      </div>

      {/* Weight Sliders */}
      <div>
        <h4 className="text-sm font-medium text-gray-500 mb-3">Adjust Weights</h4>
        <div className="space-y-4">
          {criteria.map((criterion) => (
            <WeightSlider
              key={criterion.id}
              criterionId={criterion.id}
              label={criterion.name}
              value={weights[criterion.id] ?? criterion.weight}
              onChange={onWeightChange}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
