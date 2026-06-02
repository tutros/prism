import { useState } from 'react'
import type { Criterion } from '../../lib/api'

interface Props {
  criteria: Criterion[]
  options: string[]
  weights: Record<string, number>
  onWeightChange: (criterionId: string, weight: number) => void
}

export function CriteriaSection({ criteria, options, weights, onWeightChange }: Props) {
  const [srcOpen, setSrcOpen] = useState<Record<string, boolean>>({})

  return (
    <div style={{ background: 'var(--sf)', borderRadius: 'var(--r)', border: '1px solid var(--bd)', padding: '20px 22px', marginBottom: 18 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--txb)', letterSpacing: '-0.01em' }}>What We Compared</h3>
        <span style={{ fontSize: 12, color: 'var(--txm)' }}>Slide to rebalance →</span>
      </div>

      {criteria.map((c, ci) => {
        const w = weights[c.id] ?? c.weight
        const scores = options.map(o => c.scores[o] ?? 0)
        const maxScore = Math.max(...scores, 1)
        return (
          <div key={c.id} style={{ marginBottom: 20, paddingBottom: 20, borderBottom: ci < criteria.length - 1 ? '1px solid var(--bd)' : 'none' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--txb)', marginBottom: 3 }}>{c.name}</div>
                <div style={{ fontSize: 12, color: 'var(--txm)' }}>{c.description}</div>
              </div>
              <div style={{ textAlign: 'right', flexShrink: 0, marginLeft: 16 }}>
                <div style={{ fontSize: 12, color: 'var(--txm)', marginBottom: 5 }}>
                  Weight: <b style={{ color: 'var(--ac)' }}>{Math.round(w)}%</b>
                </div>
                <input
                  type="range" min="0" max="100" value={Math.round(w)}
                  onChange={e => onWeightChange(c.id, Number(e.target.value))}
                  style={{ width: 100 }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {options.map(opt => {
                const score = c.scores[opt] ?? 0
                return (
                  <div key={opt} style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                    <span style={{ fontSize: 12, minWidth: 110, color: 'var(--tx)', fontWeight: score === maxScore ? 700 : 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{opt}</span>
                    <div style={{ flex: 1, height: 8, background: 'var(--sf2)', borderRadius: 100, overflow: 'hidden' }}>
                      <div style={{ height: '100%', borderRadius: 100, width: `${score}%`, background: score === maxScore ? 'var(--ac)' : 'var(--bd)', transition: 'width 0.4s' }} />
                    </div>
                    <span style={{ fontSize: 12, fontWeight: 600, minWidth: 26, textAlign: 'right', color: score === maxScore ? 'var(--ac)' : 'var(--txm)' }}>{score}</span>
                  </div>
                )
              })}
            </div>

            {c.sources.length > 0 && (
              <>
                <button onClick={() => setSrcOpen(p => ({ ...p, [c.id]: !p[c.id] }))}
                  style={{ marginTop: 10, fontSize: 11, color: 'var(--ac)', fontWeight: 700, background: 'none', border: 'none', cursor: 'pointer', padding: 0, fontFamily: 'inherit' }}>
                  {srcOpen[c.id] ? 'Hide sources ↑' : `View ${c.sources.length} source${c.sources.length > 1 ? 's' : ''} ↓`}
                </button>
                {srcOpen[c.id] && (
                  <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap', marginTop: 8 }}>
                    {c.sources.map(s => (
                      <span key={s} style={{ fontSize: 11, padding: '4px 11px', borderRadius: 100, background: 'var(--sf2)', color: 'var(--txm)', fontWeight: 600, border: '1px solid var(--bd)' }}>{s}</span>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        )
      })}
    </div>
  )
}
