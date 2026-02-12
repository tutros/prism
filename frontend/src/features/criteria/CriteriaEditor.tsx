import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { Criterion, SourceMetadata } from '../comparison/types'
import { SourceLink } from './SourceLink'

const API_BASE = 'http://localhost:8000'

interface CriteriaEditorProps {
  criterion: Criterion
  comparisonId: string
  optionAName: string
  optionBName: string
  weight: number
  sensitivity: number
  sourceMetadata: Record<string, SourceMetadata>
}

export function CriteriaEditor({
  criterion,
  comparisonId,
  optionAName,
  optionBName,
  weight,
  sensitivity,
  sourceMetadata,
}: CriteriaEditorProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [draft, setDraft] = useState({
    name: criterion.name,
    score_a: criterion.score_a,
    score_b: criterion.score_b,
  })
  const queryClient = useQueryClient()

  const updateMutation = useMutation({
    mutationFn: async (update: Partial<Criterion>) => {
      const res = await fetch(
        `${API_BASE}/api/comparisons/${comparisonId}/criteria/${criterion.id}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(update),
        }
      )
      if (!res.ok) throw new Error('Update failed')
      return res.json()
    },
    onMutate: async (update) => {
      await queryClient.cancelQueries({ queryKey: ['comparison', comparisonId] })
      const previous = queryClient.getQueryData(['comparison', comparisonId])

      queryClient.setQueryData(['comparison', comparisonId], (old: any) => {
        if (!old) return old
        return {
          ...old,
          criteria: old.criteria.map((c: Criterion) =>
            c.id === criterion.id ? { ...c, ...update } : c
          ),
        }
      })

      return { previous }
    },
    onError: (_err, _update, context) => {
      queryClient.setQueryData(['comparison', comparisonId], context?.previous)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['comparison', comparisonId] })
    },
  })

  const handleSave = () => {
    const changes: Partial<Criterion> = {}
    if (draft.name !== criterion.name) changes.name = draft.name
    if (draft.score_a !== criterion.score_a) changes.score_a = draft.score_a
    if (draft.score_b !== criterion.score_b) changes.score_b = draft.score_b

    if (Object.keys(changes).length > 0) {
      updateMutation.mutate(changes)
    }
    setIsEditing(false)
  }

  const handleCancel = () => {
    setDraft({
      name: criterion.name,
      score_a: criterion.score_a,
      score_b: criterion.score_b,
    })
    setIsEditing(false)
  }

  // Sensitivity badge
  const sensitivityBadge = sensitivity > 0.7 ? (
    <span className="inline-block px-2 py-0.5 text-xs font-medium bg-red-100 text-red-700 rounded">
      High Impact
    </span>
  ) : sensitivity > 0.4 ? (
    <span className="inline-block px-2 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-700 rounded">
      Medium Impact
    </span>
  ) : null

  // Confidence badge - only for AI-generated criteria
  const confidenceBadge = criterion.origin === 'ai' ? (
    criterion.confidence === 'high' ? (
      <span className="inline-block px-2 py-0.5 text-xs font-medium bg-green-100 text-green-700 rounded">
        High Confidence
      </span>
    ) : criterion.confidence === 'medium' ? (
      <span className="inline-block px-2 py-0.5 text-xs font-medium bg-amber-100 text-amber-700 rounded">
        Med Confidence
      </span>
    ) : (
      <span className="inline-block px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 rounded">
        Low Confidence
      </span>
    )
  ) : null

  if (!isEditing) {
    return (
      <div
        id={`criterion-${criterion.id}`}
        className="p-4 bg-white border border-gray-200 rounded-lg cursor-pointer hover:border-blue-300 hover:bg-blue-50/30 transition-colors scroll-mt-4"
        onClick={() => setIsEditing(true)}
      >
        <div className="flex justify-between items-start mb-2">
          <div className="flex items-start gap-2">
            <div>
              <h4 className="font-medium">{criterion.name}</h4>
              <p className="text-sm text-gray-600">{criterion.description}</p>
            </div>
            {criterion.origin === 'user' && (
              <span className="inline-block px-2 py-0.5 text-xs font-medium bg-purple-100 text-purple-700 rounded">
                Custom
              </span>
            )}
            {sensitivityBadge}
            {confidenceBadge}
          </div>
          <span className="text-sm text-blue-600 font-medium">
            Weight: {weight}%
          </span>
        </div>
        <div className="grid grid-cols-2 gap-4 mt-3">
          <div>
            <span className="text-sm text-gray-500">{optionAName}</span>
            <div className="text-lg font-semibold">
              {criterion.score_a}
              <span className="text-sm font-normal text-gray-400">/100</span>
            </div>
          </div>
          <div>
            <span className="text-sm text-gray-500">{optionBName}</span>
            <div className="text-lg font-semibold">
              {criterion.score_b}
              <span className="text-sm font-normal text-gray-400">/100</span>
            </div>
          </div>
        </div>
        {criterion.sources.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-100">
            <span className="text-xs text-gray-500">Sources: </span>
            {criterion.sources.map((src, idx) => (
              <span key={src}>
                <SourceLink
                  url={src}
                  metadata={sourceMetadata[src]}
                  comparisonId={comparisonId}
                />
                {idx < criterion.sources.length - 1 && (
                  <span className="text-xs text-gray-400">, </span>
                )}
              </span>
            ))}
          </div>
        )}
        <p className="text-xs text-gray-400 mt-2">Click to edit</p>
      </div>
    )
  }

  return (
    <div
      id={`criterion-${criterion.id}`}
      className="p-4 bg-white border-2 border-blue-500 rounded-lg scroll-mt-4"
    >
      <div className="mb-3">
        <label className="text-sm text-gray-600 block mb-1">Name</label>
        <input
          className="w-full font-medium border rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={draft.name}
          onChange={(e) => setDraft({ ...draft, name: e.target.value })}
        />
      </div>
      <div className="grid grid-cols-2 gap-4 mt-2">
        <div>
          <label className="text-sm text-gray-500 block mb-1">{optionAName} Score</label>
          <input
            type="number"
            min="0"
            max="100"
            className="w-full border rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={draft.score_a}
            onChange={(e) => setDraft({ ...draft, score_a: Number(e.target.value) })}
          />
        </div>
        <div>
          <label className="text-sm text-gray-500 block mb-1">{optionBName} Score</label>
          <input
            type="number"
            min="0"
            max="100"
            className="w-full border rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={draft.score_b}
            onChange={(e) => setDraft({ ...draft, score_b: Number(e.target.value) })}
          />
        </div>
      </div>
      <div className="flex gap-2 mt-4">
        <button
          onClick={handleSave}
          disabled={updateMutation.isPending}
          className="px-4 py-1.5 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 disabled:opacity-50"
        >
          {updateMutation.isPending ? 'Saving...' : 'Save'}
        </button>
        <button
          onClick={handleCancel}
          className="px-4 py-1.5 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
