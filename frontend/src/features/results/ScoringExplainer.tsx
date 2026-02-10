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
          <div className="border-t border-gray-200 pt-3 space-y-3">
            <p>
              <span className="font-medium text-gray-800">Each option gets its own score.</span> Think of it like a grade — both options could get an A, or both could get a C. They're not splitting points between them.
            </p>

            <p>
              <span className="font-medium text-gray-800">Weights show what matters most to you.</span> Slide them to match your priorities. Higher weight = bigger impact on the final score.
            </p>

            <p>
              <span className="font-medium text-gray-800">Impact badges</span> — Criteria marked "High Impact" or "Medium Impact" have the most influence on the winner. These are calculated from score difference × weight.
            </p>

            <p>
              <span className="font-medium text-gray-800">The final score combines everything.</span> It blends all the scores based on your weights. The higher the number, the better that option fits your priorities.
            </p>
          </div>

          <div className="bg-white border border-gray-200 rounded p-3 text-xs text-gray-600">
            <span className="font-medium">Try it:</span> Move a weight slider and watch the final scores update instantly.
          </div>

          <p className="text-xs text-gray-500">
            Scores come from AI analysis of real web sources. Click any source link to verify.
          </p>
        </div>
      )}
    </div>
  )
}
