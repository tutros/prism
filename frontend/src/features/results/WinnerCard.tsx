import type { AnalysisResult } from '../../lib/api'
import { calcWeightedScores } from '../../lib/scoring'
import { CONFIDENCE_STYLE, overallConfidence } from '../../lib/confidence'

interface Props {
  result: AnalysisResult
  weights: Record<string, number>
}

export function WinnerCard({ result, weights }: Props) {
  const scores = calcWeightedScores(result.criteria, result.options, weights)
  const winner = scores[0]
  const conf = overallConfidence(result)
  const confStyle = conf ? CONFIDENCE_STYLE[conf] : null
  const maxScore = scores[0]?.score ?? 1

  if (!winner) return null

  return (
    <div style={{
      borderRadius: 20, padding: 26, marginBottom: 22,
      background: 'linear-gradient(135deg,#ece8ff 0%,#e5efff 100%)',
      border: '2px solid #c4b5fd', boxShadow: '0 4px 28px rgba(91,61,245,.1)',
    }}>
      <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
        <div style={{
          width: 52, height: 52, borderRadius: 16, background: 'var(--ac)', color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, flexShrink: 0,
        }}>🏆</div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', gap: 8, marginBottom: 6, flexWrap: 'wrap', alignItems: 'center' }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--ac)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
              Our Recommendation
            </span>
            {confStyle && (
              <span style={{ fontSize: 11, fontWeight: 700, padding: '2px 10px', borderRadius: 100, background: confStyle.bg, color: confStyle.color }}>
                {confStyle.label}
              </span>
            )}
            {result.tier === 'quick' && (
              <span style={{ fontSize: 11, color: 'var(--txm)' }}>
                Based on AI knowledge only, no sources
              </span>
            )}
          </div>
          <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--txb)', letterSpacing: '-0.03em', marginBottom: 8 }}>
            {winner.option}
          </div>
          {result.reasoning && (
            <p style={{ fontSize: 14, color: 'var(--tx)', lineHeight: 1.7 }}>{result.reasoning}</p>
          )}
        </div>
        <div style={{ textAlign: 'center', flexShrink: 0 }}>
          <div style={{ fontSize: 36, fontWeight: 800, color: 'var(--ac)', letterSpacing: '-0.02em', lineHeight: 1 }}>
            {winner.score.toFixed(0)}
          </div>
          <div style={{ fontSize: 11, color: 'var(--txm)', fontWeight: 600 }}>/100</div>
        </div>
      </div>

      {scores.length > 1 && (
        <div style={{ marginTop: 20, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {scores.map((s, i) => (
            <div key={s.option} style={{ flex: 1, minWidth: 80 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: i === 0 ? 'var(--ac)' : 'var(--txm)', marginBottom: 4 }}>
                {i === 0 ? '✓ ' : ''}{s.option}
              </div>
              <div style={{ height: 6, background: 'rgba(91,61,245,.12)', borderRadius: 100, overflow: 'hidden' }}>
                <div style={{
                  height: '100%', borderRadius: 100, background: i === 0 ? 'var(--ac)' : '#c4b5fd',
                  width: `${(s.score / maxScore) * 100}%`, transition: 'width 0.6s ease',
                }} />
              </div>
              <div style={{ fontSize: 11, color: 'var(--txm)', marginTop: 3 }}>{s.score.toFixed(1)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
