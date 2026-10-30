import { describe, it, expect } from 'vitest'
import { isGraded, overallConfidence } from './confidence'
import type { AnalysisResult, Criterion, Tier } from './api'

type Conf = Criterion['confidence']

const crit = (confidence: Conf, origin: Criterion['origin'] = 'ai'): Criterion => ({
  id: Math.random().toString(), name: 'c', description: '', scores: {}, weight: 50,
  sources: [], origin, confidence,
})

const result = (criteria: Criterion[], tier: Tier = 'medium'): AnalysisResult => ({
  analysis_id: 'a', decision_id: 'd', tier, status: 'completed', options: ['A', 'B'],
  winner: 'A', reasoning: '', criteria, weights_original: {}, weights_current: {},
  research: {}, source_quality: {}, hidden_properties: [], created_at: '', completed_at: null,
})

describe('isGraded', () => {
  it('grades AI criteria with a confidence on Medium/Deep', () => {
    expect(isGraded(crit('low'), 'medium')).toBe(true)
    expect(isGraded(crit('high'), 'deep')).toBe(true)
  })

  it('does not grade Quick criteria, even ones saved with a confidence', () => {
    expect(isGraded(crit('low'), 'quick')).toBe(false)
  })

  it('does not grade user-added criteria, even ones saved with a confidence', () => {
    expect(isGraded(crit('low', 'user'), 'medium')).toBe(false)
  })

  it('does not grade criteria with no confidence', () => {
    expect(isGraded(crit(null), 'medium')).toBe(false)
  })
})

describe('overallConfidence', () => {
  it('is high when at least half the graded criteria are high', () => {
    expect(overallConfidence(result([crit('high'), crit('low')]))).toBe('high')
  })

  it('is medium when a quarter to a half are high', () => {
    expect(overallConfidence(result([crit('high'), crit('low'), crit('low'), crit('medium')]))).toBe('medium')
  })

  it('is low when under a quarter are high', () => {
    expect(overallConfidence(result([crit('medium'), crit('low'), crit('low')]))).toBe('low')
  })

  it('ignores user-added criteria', () => {
    // Counting the 2 user criteria would make it 1/4 high (medium)
    const criteria = [crit('high'), crit('low'), crit('low', 'user'), crit(null, 'user')]
    expect(overallConfidence(result(criteria))).toBe('high')
  })

  it('is null when nothing is graded', () => {
    expect(overallConfidence(result([crit(null, 'user')]))).toBeNull()
    expect(overallConfidence(result([]))).toBeNull()
  })

  it('is null for Quick results', () => {
    expect(overallConfidence(result([crit('high'), crit('high')], 'quick'))).toBeNull()
  })
})
