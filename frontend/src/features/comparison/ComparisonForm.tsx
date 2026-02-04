import { useState } from 'react'
import { useComparison } from './useComparison'

interface ComparisonFormProps {
  onSubmit: (comparisonId: string) => void
}

export function ComparisonForm({ onSubmit }: ComparisonFormProps) {
  const [optionA, setOptionA] = useState('')
  const [optionB, setOptionB] = useState('')
  const [intent, setIntent] = useState('')

  const mutation = useComparison()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!optionA.trim() || !optionB.trim() || !intent.trim()) {
      return
    }

    mutation.mutate(
      { option_a: optionA, option_b: optionB, intent },
      {
        onSuccess: (data) => {
          onSubmit(data.comparison_id)
        },
      }
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="optionA" className="block text-sm font-medium text-gray-700 mb-1">
            Option A
          </label>
          <input
            id="optionA"
            type="text"
            value={optionA}
            onChange={(e) => setOptionA(e.target.value)}
            placeholder="e.g., Glass bottle"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
        </div>
        <div>
          <label htmlFor="optionB" className="block text-sm font-medium text-gray-700 mb-1">
            Option B
          </label>
          <input
            id="optionB"
            type="text"
            value={optionB}
            onChange={(e) => setOptionB(e.target.value)}
            placeholder="e.g., Plastic bottle"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
        </div>
      </div>

      <div>
        <label htmlFor="intent" className="block text-sm font-medium text-gray-700 mb-1">
          Your Intent / Priorities
        </label>
        <textarea
          id="intent"
          value={intent}
          onChange={(e) => setIntent(e.target.value)}
          placeholder="e.g., I want to minimize environmental impact in my local community"
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          required
        />
      </div>

      <button
        type="submit"
        disabled={mutation.isPending}
        className="w-full md:w-auto px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
      >
        {mutation.isPending ? 'Comparing...' : 'Compare'}
      </button>

      {mutation.isError && (
        <p className="text-red-600 text-sm">
          Error: {mutation.error.message}
        </p>
      )}
    </form>
  )
}
