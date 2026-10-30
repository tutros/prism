import type { AnalysisResult, Criterion, Tier } from './api'

export type Confidence = 'high' | 'medium' | 'low'

/**
 * Whether a criterion carries a source-based confidence grade.
 * Quick-tier criteria (no sources) and user-added criteria are never graded,
 * including ones stored before grading existed with a default "low".
 */
export function isGraded(c: Criterion, tier: Tier): boolean {
  return tier !== 'quick' && c.origin === 'ai' && c.confidence != null
}

/**
 * Overall confidence for the winner card, from the share of graded criteria
 * rated high. Null when nothing is graded (no badge is shown).
 */
export function overallConfidence(result: AnalysisResult): Confidence | null {
  const graded = result.criteria.filter(c => isGraded(c, result.tier))
  if (graded.length === 0) return null
  const highShare = graded.filter(c => c.confidence === 'high').length / graded.length
  if (highShare >= 0.5) return 'high'
  if (highShare >= 0.25) return 'medium'
  return 'low'
}

export const CONFIDENCE_STYLE: Record<Confidence, { bg: string; color: string; label: string }> = {
  high:   { bg: '#dcfce7', color: '#16a34a', label: 'High Confidence' },
  medium: { bg: '#fef3c7', color: '#d97706', label: 'Medium Confidence' },
  low:    { bg: '#fee2e2', color: '#dc2626', label: 'Low Confidence' },
}
