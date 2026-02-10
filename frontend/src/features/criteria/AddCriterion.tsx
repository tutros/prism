import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiPost } from '../../lib/api'
import type { Criterion } from '../comparison/types'

interface AddCriterionProps {
  comparisonId: string
  optionAName: string
  optionBName: string
}

export function AddCriterion({ comparisonId, optionAName, optionBName }: AddCriterionProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [form, setForm] = useState({
    name: '',
    description: '',
    score_a: 50,
    score_b: 50,
    weight: 50,
  })
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: async () => {
      // apiPost already returns parsed JSON and throws on error
      return apiPost<Criterion>(`/api/comparisons/${comparisonId}/criteria`, form)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['results', comparisonId] })
      setForm({ name: '', description: '', score_a: 50, score_b: 50, weight: 50 })
      setIsOpen(false)
    },
  })

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="w-full p-4 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-blue-400 hover:text-blue-600 transition-colors"
      >
        + Add Custom Criterion
      </button>
    )
  }

  return (
    <div className="p-4 bg-white border-2 border-blue-500 rounded-lg">
      <h4 className="font-medium mb-3">Add Custom Criterion</h4>

      <div className="space-y-3">
        <div>
          <label className="text-sm text-gray-600 block mb-1">Name *</label>
          <input
            className="w-full border rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., Personal Preference"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
        </div>

        <div>
          <label className="text-sm text-gray-600 block mb-1">Description *</label>
          <textarea
            className="w-full border rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Why this criterion matters to you..."
            rows={2}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-gray-500 block mb-1">{optionAName} Score</label>
            <input
              type="number"
              min="0"
              max="100"
              className="w-full border rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={form.score_a}
              onChange={(e) => setForm({ ...form, score_a: Number(e.target.value) })}
            />
          </div>
          <div>
            <label className="text-sm text-gray-500 block mb-1">{optionBName} Score</label>
            <input
              type="number"
              min="0"
              max="100"
              className="w-full border rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={form.score_b}
              onChange={(e) => setForm({ ...form, score_b: Number(e.target.value) })}
            />
          </div>
        </div>

        <div>
          <label className="text-sm text-gray-600 block mb-1">Weight (0-100)</label>
          <input
            type="number"
            min="0"
            max="100"
            className="w-full border rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={form.weight}
            onChange={(e) => setForm({ ...form, weight: Number(e.target.value) })}
          />
        </div>
      </div>

      <div className="flex gap-2 mt-4">
        <button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending || !form.name || !form.description}
          className="px-4 py-1.5 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {mutation.isPending ? 'Adding...' : 'Add Criterion'}
        </button>
        <button
          onClick={() => setIsOpen(false)}
          className="px-4 py-1.5 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
