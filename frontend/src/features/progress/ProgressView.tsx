import { useEffect } from 'react'
import { useProgress } from './useProgress'
import { useResults } from '../results/useResults'

interface Props {
  analysisId: string
  onComplete: () => void
}

const TIER_EMOJI: Record<string, string> = { quick: '⚡', medium: '🔍', deep: '🔬' }

export function ProgressView({ analysisId, onComplete }: Props) {
  const { messages } = useProgress(analysisId)
  const { data: result } = useResults(analysisId)

  useEffect(() => {
    if (result?.status === 'completed' || result?.status === 'error') {
      onComplete()
    }
  }, [result?.status, onComplete])

  const latest = messages[messages.length - 1] ?? 'Starting…'
  const tier = result?.tier ?? 'medium'
  const options = result?.options ?? []

  return (
    <div style={{ maxWidth: 500, margin: '60px auto', textAlign: 'center' }}>
      <div style={{ fontSize: 52, marginBottom: 18 }}>{TIER_EMOJI[tier]}</div>
      <h2 style={{ fontSize: 24, fontWeight: 800, color: 'var(--txb)', marginBottom: 8, letterSpacing: '-0.03em' }}>
        Analyzing your options…
      </h2>
      <p style={{ fontSize: 14, color: 'var(--txm)', marginBottom: 32, minHeight: 22 }}>{latest}</p>

      <div style={{ background: 'var(--bd)', borderRadius: 100, height: 8, overflow: 'hidden', marginBottom: 10 }}>
        <div style={{
          height: '100%', background: 'var(--ac)', borderRadius: 100,
          width: messages.length > 0 ? '66%' : '10%',
          transition: 'width 0.5s cubic-bezier(.4,0,.2,1)',
          boxShadow: '0 0 16px rgba(91,61,245,.5)',
          animation: 'pulse-bar 2s ease-in-out infinite',
        }} />
      </div>
      <p style={{ fontSize: 13, color: 'var(--txm)', marginBottom: 32 }}>Processing…</p>

      {options.length > 0 && (
        <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
          {options.map(o => (
            <span key={o} style={{ padding: '6px 14px', borderRadius: 100, background: 'var(--ac-dim)', color: 'var(--ac)', fontSize: 13, fontWeight: 600 }}>{o}</span>
          ))}
        </div>
      )}
    </div>
  )
}
