import type { Criterion } from './api'

export interface OptionScore {
  option: string
  score: number
}

/**
 * Calculates weighted scores for each option across all criteria.
 * Weights are normalised to sum to 100 before scoring.
 * Returns entries sorted by score descending.
 */
export function calcWeightedScores(
  criteria: Criterion[],
  options: string[],
  weightOverrides?: Record<string, number>,
): OptionScore[] {
  const weights = criteria.map(c => weightOverrides?.[c.id] ?? c.weight)
  const totalWeight = weights.reduce((s, w) => s + w, 0)

  return options
    .map(option => {
      const score =
        totalWeight === 0
          ? 0
          : criteria.reduce((sum, c, i) => {
              const s = c.scores[option] ?? 0
              return sum + s * (weights[i] / totalWeight)
            }, 0)
      return { option, score: Math.round(score * 10) / 10 }
    })
    .sort((a, b) => b.score - a.score)
}
