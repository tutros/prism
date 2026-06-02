import { useState } from 'react'
import { apiPost } from '../../lib/api'
import type { DecisionInput, CreateDecisionResponse, Tier } from '../../lib/api'

interface Props {
  onAnalysisCreated: (decisionId: string, analysisId: string) => void
}

const TIER_INFO = [
  { id: 'quick'  as Tier, em: '⚡', label: 'Quick',  sub: 'LLM knowledge only',        time: '~5 sec',  cost: '$0.002', color: '#e8a600' },
  { id: 'medium' as Tier, em: '🔍', label: 'Medium', sub: 'Web research + sources',    time: '~45 sec', cost: '$0.04',  color: '#5b3df5' },
  { id: 'deep'   as Tier, em: '🔬', label: 'Deep',   sub: 'Hidden property discovery', time: '~3 min',  cost: '$0.18',  color: '#059669' },
]

export function DecisionForm({ onAnalysisCreated }: Props) {
  const [intent, setIntent] = useState('')
  const [options, setOptions] = useState(['', ''])
  const [contexts, setContexts] = useState<Record<number, string>>({})
  const [ctxOpen, setCtxOpen] = useState<Record<number, boolean>>({})
  const [tier, setTier] = useState<Tier>('medium')
  const [suggestedTier, setSuggestedTier] = useState<Tier | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const setOption = (i: number, v: string) =>
    setOptions(prev => prev.map((o, idx) => idx === i ? v : o))

  const addOption = () => {
    if (options.length >= 6) return
    setOptions(prev => [...prev, ''])
  }

  const removeOption = (i: number) => {
    if (options.length <= 2) return
    setOptions(prev => prev.filter((_, idx) => idx !== i))
    setContexts(prev => {
      const next = { ...prev }
      delete next[i]
      return next
    })
  }

  const validate = (): string | null => {
    if (!intent.trim()) return 'Please describe your decision.'
    const filled = options.filter(o => o.trim())
    if (filled.length < 2) return 'Please enter at least 2 options.'
    return null
  }

  const handleSubmit = async () => {
    const err = validate()
    if (err) { setError(err); return }
    setError(null)
    setLoading(true)
    try {
      const filledOptions = options.filter(o => o.trim())
      const option_contexts: Record<string, string> = {}
      filledOptions.forEach((opt, i) => {
        if (contexts[i]?.trim()) option_contexts[opt] = contexts[i].trim()
      })

      const body: DecisionInput = { options: filledOptions, option_contexts, intent: intent.trim() }
      const { decision_id, suggested_tier } = await apiPost<CreateDecisionResponse>('/api/decisions', body)
      setSuggestedTier(suggested_tier)

      const { analysis_id } = await apiPost<{ analysis_id: string }>(
        `/api/decisions/${decision_id}/analyses`, { tier }
      )
      onAnalysisCreated(decision_id, analysis_id)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: 30, fontWeight: 800, color: 'var(--txb)', marginBottom: 6, letterSpacing: '-0.03em', lineHeight: 1.15 }}>
        What are you deciding?
      </h1>
      <p style={{ fontSize: 14, color: 'var(--txm)', marginBottom: 28 }}>
        Describe your options and we'll surface the tradeoffs that matter most.
      </p>

      {/* Decision */}
      <div style={{ background: 'var(--sf)', borderRadius: 'var(--r)', border: '1px solid var(--bd)', padding: '20px 22px', marginBottom: 16 }}>
        <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: 'var(--txm)', letterSpacing: '0.07em', textTransform: 'uppercase', marginBottom: 10 }}>
          Your Decision
        </label>
        <textarea
          value={intent}
          onChange={e => setIntent(e.target.value)}
          placeholder="e.g. Choosing a cloud database for our SaaS startup"
          style={{
            width: '100%', border: '2px solid var(--bd)', borderRadius: 11, padding: '11px 14px',
            fontSize: 14, fontFamily: 'inherit', resize: 'none', height: 76, outline: 'none',
            color: 'var(--txb)', background: 'var(--sf2)', lineHeight: 1.5,
          }}
          onFocus={e => (e.target.style.borderColor = 'var(--ac)')}
          onBlur={e => (e.target.style.borderColor = 'var(--bd)')}
        />

        {/* Options */}
        <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: 'var(--txm)', letterSpacing: '0.07em', textTransform: 'uppercase', margin: '20px 0 10px' }}>
          Options {options.length >= 6 && <span style={{ color: '#d97706', fontWeight: 600, textTransform: 'none', letterSpacing: 0 }}>· 6 max recommended</span>}
        </label>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {options.map((opt, i) => (
            <div key={i}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, background: 'var(--sf2)', borderRadius: 11, padding: '11px 14px', border: '2px solid var(--bd)' }}>
                <div style={{ width: 28, height: 28, borderRadius: 8, background: 'var(--ac)', color: '#fff', fontSize: 12, fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  {i + 1}
                </div>
                <input
                  value={opt}
                  onChange={e => setOption(i, e.target.value)}
                  placeholder={`Option ${i + 1}`}
                  style={{ flex: 1, background: 'transparent', border: 'none', outline: 'none', fontSize: 13, fontWeight: 600, color: 'var(--txb)', fontFamily: 'inherit' }}
                />
                <button
                  onClick={() => setCtxOpen(p => ({ ...p, [i]: !p[i] }))}
                  style={{ fontSize: 11, color: 'var(--ac)', fontWeight: 700, background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'inherit', flexShrink: 0 }}
                >
                  {ctxOpen[i] ? 'Less ↑' : 'Details +'}
                </button>
                {options.length > 2 && (
                  <button
                    onClick={() => removeOption(i)}
                    style={{ fontSize: 16, color: 'var(--txm)', background: 'none', border: 'none', cursor: 'pointer', lineHeight: 1, padding: '0 2px' }}
                  >×</button>
                )}
              </div>
              {ctxOpen[i] && (
                <div style={{ border: '2px solid var(--bd)', borderTop: 'none', borderRadius: '0 0 11px 11px', padding: '10px 14px', background: 'var(--sf2)' }}>
                  <textarea
                    value={contexts[i] ?? ''}
                    onChange={e => setContexts(p => ({ ...p, [i]: e.target.value }))}
                    placeholder="Add description, links, or notes…"
                    style={{ width: '100%', background: 'transparent', border: 'none', outline: 'none', fontSize: 12, fontFamily: 'inherit', color: 'var(--tx)', resize: 'none', height: 52, lineHeight: 1.5 }}
                  />
                </div>
              )}
            </div>
          ))}
          {options.length < 8 && (
            <button
              onClick={addOption}
              style={{ borderRadius: 11, padding: '11px 14px', border: '2px dashed var(--bd)', background: 'none', cursor: 'pointer', fontSize: 13, color: 'var(--txm)', fontWeight: 600, fontFamily: 'inherit', textAlign: 'left' }}
              onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--ac)'; (e.currentTarget as HTMLElement).style.color = 'var(--ac)' }}
              onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--bd)'; (e.currentTarget as HTMLElement).style.color = 'var(--txm)' }}
            >
              + Add Option
            </button>
          )}
        </div>
      </div>

      {/* Tier */}
      <div style={{ background: 'var(--sf)', borderRadius: 'var(--r)', border: '1px solid var(--bd)', padding: '20px 22px', marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <label style={{ fontSize: 11, fontWeight: 700, color: 'var(--txm)', letterSpacing: '0.07em', textTransform: 'uppercase' }}>
            How Deep?
          </label>
          {suggestedTier && (
            <span style={{ fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 20, background: '#e7f5e8', color: '#16a34a' }}>
              ✨ Suggested: {suggestedTier.charAt(0).toUpperCase() + suggestedTier.slice(1)}
            </span>
          )}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12 }}>
          {TIER_INFO.map(t => (
            <button
              key={t.id}
              onClick={() => setTier(t.id)}
              style={{
                padding: '16px 14px', borderRadius: 14, cursor: 'pointer', textAlign: 'left',
                border: tier === t.id ? `2px solid ${t.color}` : '2px solid var(--bd)',
                background: tier === t.id ? `${t.color}18` : 'var(--sf2)',
                fontFamily: 'inherit', transition: 'all 0.15s',
              }}
            >
              <div style={{ fontSize: 26, marginBottom: 8 }}>{t.em}</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: tier === t.id ? t.color : 'var(--txb)', marginBottom: 3 }}>{t.label}</div>
              <div style={{ fontSize: 11, color: 'var(--txm)', lineHeight: 1.4, marginBottom: 8 }}>{t.sub}</div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 11, color: tier === t.id ? t.color : 'var(--txm)', fontWeight: 600 }}>{t.time}</span>
                <span style={{ fontSize: 11, color: tier === t.id ? t.color : 'var(--txm)', fontWeight: 600 }}>{t.cost}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {error && (
        <p style={{ color: '#dc2626', fontSize: 13, marginBottom: 12, fontWeight: 600 }}>{error}</p>
      )}

      <button
        onClick={handleSubmit}
        disabled={loading}
        style={{
          width: '100%', padding: 15, borderRadius: 13, border: 'none',
          background: loading ? 'var(--bd)' : 'var(--ac)', color: loading ? 'var(--txm)' : '#fff',
          fontSize: 15, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer',
          boxShadow: loading ? 'none' : '0 4px 20px rgba(91,61,245,.28)', fontFamily: 'inherit',
          transition: 'all 0.15s',
        }}
      >
        {loading ? 'Starting analysis…' : 'Analyze Now →'}
      </button>
    </div>
  )
}
