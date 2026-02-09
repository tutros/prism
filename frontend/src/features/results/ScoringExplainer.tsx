import { useState } from 'react'

export function ScoringExplainer() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="border border-gray-200 rounded-lg bg-gray-50">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 flex items-center justify-between text-left text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors rounded-lg"
      >
        <span className="flex items-center gap-2">
          <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          How does scoring work?
        </span>
        <svg
          className={`w-4 h-4 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="px-4 pb-4 text-sm text-gray-600 space-y-3">
          <div className="border-t border-gray-200 pt-3">
            <p className="font-medium text-gray-800 mb-2">Understanding the Scores</p>

            <div className="space-y-2">
              <p>
                <span className="font-medium">Criterion scores (0-100):</span> Each option is rated independently on how well it performs for each criterion. A score of 80 means "performs well," not "gets 80% of the points." Both options can score high, or both can score low.
              </p>

              <p>
                <span className="font-medium">Weights (importance):</span> Weights reflect how much each criterion matters to your decision. A criterion with 30% weight has 3x more influence than one with 10%. Adjust the sliders to match your priorities.
              </p>

              <p>
                <span className="font-medium">Final score:</span> The weighted average of all criterion scores. Higher score = better overall performance based on your weighted priorities.
              </p>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded p-3">
            <p className="text-xs text-gray-500 mb-1">Example calculation:</p>
            <p className="text-xs font-mono text-gray-700">
              If Criterion A (weight 60%) scores 80, and Criterion B (weight 40%) scores 50:<br/>
              Final = (80 × 0.6) + (50 × 0.4) = 48 + 20 = <span className="font-bold">68</span>
            </p>
          </div>

          <p className="text-xs text-gray-500 italic">
            Scores are based on AI analysis of web sources. Adjust weights to explore how different priorities affect the outcome.
          </p>
        </div>
      )}
    </div>
  )
}
