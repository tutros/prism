import { useState } from 'react'
import { useResults } from './useResults'
import { WinnerCard } from './WinnerCard'
import { CriteriaSection } from './CriteriaSection'
import { HiddenPropertiesSection } from './HiddenPropertiesSection'

interface Props {
  decisionId: string
  analysisId: string
}

export function ResultsDisplay({ decisionId, analysisId }: Props) {
  const { data: result, isLoading, error } = useResults(analysisId, decisionId)
  const [weights, setWeights] = useState<Record<string, number>>({})

  const handleWeightChange = (id: string, value: number) =>
    setWeights(prev => ({ ...prev, [id]: value }))

  if (isLoading || !result) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, color: 'var(--txm)', padding: 32 }}>
        <svg style={{ width: 20, height: 20 }} viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" opacity="0.25" />
          <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        Loading results…
      </div>
    )
  }

  if (error) return <p style={{ color: '#dc2626', padding: 32 }}>Failed to load: {(error as Error).message}</p>
  if (result.status === 'error') return <p style={{ color: '#dc2626', padding: 32 }}>Analysis failed: {result.reasoning}</p>
  if (result.status === 'processing') return <p style={{ color: 'var(--txm)', padding: 32 }}>Still processing…</p>

  const effectiveWeights = Object.fromEntries(
    result.criteria.map(c => [c.id, weights[c.id] ?? c.weight])
  )

  return (
    <div>
      <WinnerCard result={result} weights={effectiveWeights} />
      <CriteriaSection
        tier={result.tier}
        criteria={result.criteria}
        options={result.options}
        weights={effectiveWeights}
        onWeightChange={handleWeightChange}
      />
      {result.tier === 'deep' && result.hidden_properties.length > 0 && (
        <HiddenPropertiesSection properties={result.hidden_properties} />
      )}
    </div>
  )
}
