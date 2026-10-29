import { useState, useMemo } from 'react'
import type { Criterion } from '../comparison/types'

export interface WeightedScores {
  totalA: number
  totalB: number
  winner: 'a' | 'b' | 'tie'
}

export function calculateScores(
  criteria: Criterion[],
  weights: Record<string, number>
): WeightedScores {
  if (criteria.length === 0) {
    return { totalA: 0, totalB: 0, winner: 'tie' }
  }

  // Normalize weights to sum to 100
  const totalWeight = Object.values(weights).reduce((sum, w) => sum + w, 0)
  const normalizer = totalWeight > 0 ? 100 / totalWeight : 1

  let totalA = 0
  let totalB = 0

  for (const criterion of criteria) {
    const weight = (weights[criterion.id] ?? criterion.weight) * normalizer / 100
    totalA += criterion.score_a * weight
    totalB += criterion.score_b * weight
  }

  // Round to 1 decimal
  totalA = Math.round(totalA * 10) / 10
  totalB = Math.round(totalB * 10) / 10

  let winner: 'a' | 'b' | 'tie'
  if (totalA > totalB) {
    winner = 'a'
  } else if (totalB > totalA) {
    winner = 'b'
  } else {
    winner = 'tie'
  }

  return { totalA, totalB, winner }
}

interface WeightOverrides {
  key: string // criteria IDs the overrides belong to
  weights: Record<string, number>
}

export function useWeightedScores(criteria: Criterion[]) {
  const criteriaKey = criteria.map(c => c.id).join(',')
  const defaults = useMemo(() => {
    const d: Record<string, number> = {}
    for (const c of criteria) {
      d[c.id] = c.weight
    }
    return d
  }, [criteria])

  // User overrides are tagged with the criteria set they were made for, so
  // switching comparisons (new IDs) falls back to that comparison's defaults
  // without resetting state from an effect.
  const [overrides, setOverrides] = useState<WeightOverrides | null>(null)
  const weights = overrides?.key === criteriaKey ? overrides.weights : defaults

  const scores = useMemo(
    () => calculateScores(criteria, weights),
    [criteria, weights]
  )

  const updateWeight = (criterionId: string, value: number) => {
    setOverrides((prev) => ({
      key: criteriaKey,
      weights: { ...(prev?.key === criteriaKey ? prev.weights : defaults), [criterionId]: value },
    }))
  }

  return { weights, scores, updateWeight }
}
