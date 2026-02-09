export interface ComparisonInput {
  option_a: string
  option_b: string
  intent: string
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
}

export interface SubmitResponse {
  comparison_id: string
}
