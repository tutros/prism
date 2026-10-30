export const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

export async function apiPost<T>(endpoint: string, data: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    let message = `API error: ${res.status}`
    try {
      const body = await res.json()
      if (body.detail) message = body.detail
    } catch { /* ignore */ }
    throw new Error(message)
  }
  return res.json()
}

export async function apiGet<T>(endpoint: string): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`)
  if (!res.ok) {
    if (res.status === 404) throw new Error('Not found')
    throw new Error(`API error: ${res.status}`)
  }
  return res.json()
}

// ── Domain types ──────────────────────────────────────────────────────────────

export type Tier = 'quick' | 'medium' | 'deep'

export interface DecisionInput {
  options: string[]
  option_contexts: Record<string, string>
  intent: string
  tier?: Tier
}

export interface CreateDecisionResponse {
  decision_id: string
  suggested_tier: Tier
  rationale: string
}

export interface DecisionSummary {
  decision_id: string
  title: string
  options: string[]
  intent: string
  created_at: string
}

export interface HiddenProperty {
  name: string
  category: string
  magnitude: 'High' | 'Medium' | 'Low'
  confidence: 'high' | 'medium' | 'low'
  description: string
}

export interface Criterion {
  id: string
  name: string
  description: string
  scores: Record<string, number>  // keyed by option name, 0–100
  weight: number
  sources: string[]
  origin: 'ai' | 'user'
  confidence: 'high' | 'medium' | 'low' | null  // null = not graded (Quick, user-added)
}

export interface AnalysisResult {
  analysis_id: string
  decision_id: string
  tier: Tier
  status: 'processing' | 'completed' | 'error'
  options: string[]
  winner: string | null
  reasoning: string
  criteria: Criterion[]
  weights_original: Record<string, number>
  weights_current: Record<string, number>
  research: Record<string, unknown>
  source_quality: Record<string, string>  // url -> peer-reviewed / government / industry / news / blog / unknown
  hidden_properties: HiddenProperty[]
  created_at: string
  completed_at: string | null
}
