export interface ComparisonInput {
  option_a: string
  option_b: string
  intent: string
}

export type SourceQuality = 'peer-reviewed' | 'government' | 'industry' | 'news' | 'blog' | 'unknown'

export type ConfidenceLevel = 'high' | 'medium' | 'low'

export interface SourceMetadata {
  quality: SourceQuality
  flagged: boolean
  last_verified: string | null
}

export interface Criterion {
  id: string
  name: string
  description: string
  score_a: number
  score_b: number
  weight: number
  sources: string[]
  origin: 'ai' | 'user'
  confidence: ConfidenceLevel
}

export interface ComparisonResult {
  comparison_id: string
  status: 'processing' | 'completed' | 'error'
  option_a_name: string
  option_b_name: string
  intent: string
  criteria: Criterion[]
  winner: 'a' | 'b' | 'tie' | null
  reasoning: string
  created_at: string
  completed_at: string | null
  source_metadata: Record<string, SourceMetadata>
}

export interface SubmitResponse {
  comparison_id: string
}

export interface ActionableSuggestion {
  action: string
  affected_criterion: string
  impact: string
  sources: string[]
}

export interface FlipAnalysisResponse {
  suggestions: ActionableSuggestion[]
  sensitivity: Record<string, number>
}
