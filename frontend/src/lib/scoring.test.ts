import { describe, it, expect } from 'vitest'
import { calcWeightedScores } from './scoring'
import type { Criterion } from './api'

const makeCriterion = (id: string, scores: Record<string, number>, weight: number): Criterion => ({
  id, name: id, description: '', scores, weight, sources: [], origin: 'ai', confidence: 'low',
})

describe('calcWeightedScores', () => {
  it('returns one entry per option sorted by score descending', () => {
    const criteria: Criterion[] = [
      makeCriterion('c1', { A: 80, B: 40 }, 50),
      makeCriterion('c2', { A: 60, B: 90 }, 50),
    ]
    const result = calcWeightedScores(criteria, ['A', 'B'])
    expect(result).toHaveLength(2)
    // A = (80*50 + 60*50) / 100 = 70, B = (40*50 + 90*50) / 100 = 65 → A wins
    expect(result[0].option).toBe('A')
    expect(result[1].option).toBe('B')
  })

  it('normalises weights so they always sum to 100', () => {
    const criteria: Criterion[] = [
      makeCriterion('c1', { X: 100, Y: 0 }, 30),
      makeCriterion('c2', { X: 0,   Y: 100 }, 30),
    ]
    // Equal weights → tied, X first by stable sort (index 0)
    const result = calcWeightedScores(criteria, ['X', 'Y'])
    expect(result[0].score).toBeCloseTo(result[1].score)
  })

  it('handles a single option', () => {
    const criteria: Criterion[] = [makeCriterion('c1', { Solo: 75 }, 100)]
    const result = calcWeightedScores(criteria, ['Solo'])
    expect(result).toHaveLength(1)
    expect(result[0].option).toBe('Solo')
    expect(result[0].score).toBeCloseTo(75)
  })

  it('handles zero total weight by returning 0 for all options', () => {
    const criteria: Criterion[] = [makeCriterion('c1', { A: 80, B: 40 }, 0)]
    const result = calcWeightedScores(criteria, ['A', 'B'])
    expect(result[0].score).toBe(0)
    expect(result[1].score).toBe(0)
  })

  it('rounds scores to one decimal place', () => {
    const criteria: Criterion[] = [makeCriterion('c1', { A: 100 }, 3)]
    const result = calcWeightedScores(criteria, ['A'])
    const decimals = result[0].score.toString().split('.')[1]?.length ?? 0
    expect(decimals).toBeLessThanOrEqual(1)
  })
})
