import { useState } from 'react'
import type { HiddenProperty } from '../../lib/api'

interface Props {
  properties: HiddenProperty[]
}

const MAG_STYLE: Record<string, { bg: string; color: string }> = {
  High:   { bg: '#fee2e2', color: '#dc2626' },
  Medium: { bg: '#fef3c7', color: '#d97706' },
  Low:    { bg: 'var(--sf2)', color: 'var(--txm)' },
}

const CONF_STYLE: Record<string, { bg: string; color: string }> = {
  high:   { bg: '#dcfce7', color: '#16a34a' },
  medium: { bg: '#fef3c7', color: '#d97706' },
  low:    { bg: 'var(--sf2)', color: 'var(--txm)' },
}

export function HiddenPropertiesSection({ properties }: Props) {
  const [open, setOpen] = useState(false)

  return (
    <div style={{ borderRadius: 18, overflow: 'hidden', background: 'linear-gradient(135deg,#fdf4ff 0%,#f0f8ff 100%)', border: '1px solid #e9d5ff', marginBottom: 18 }}>
      <button onClick={() => setOpen(p => !p)}
        style={{ width: '100%', padding: '18px 22px', background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontFamily: 'inherit' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 22 }}>🔮</span>
          <div style={{ textAlign: 'left' }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--txb)' }}>Hidden Properties Discovered</div>
            <div style={{ fontSize: 12, color: 'var(--txm)' }}>{properties.length} non-obvious factor{properties.length !== 1 ? 's' : ''} found</div>
          </div>
        </div>
        <span style={{ fontSize: 13, color: 'var(--ac)', fontWeight: 700 }}>{open ? 'Collapse ↑' : 'Expand ↓'}</span>
      </button>

      {open && (
        <div style={{ borderTop: '1px solid #e9d5ff', padding: '0 22px 22px' }}>
          {properties.map((h, i) => {
            const mag = MAG_STYLE[h.magnitude] ?? MAG_STYLE.Low
            const conf = CONF_STYLE[h.confidence] ?? CONF_STYLE.low
            return (
              <div key={i} style={{ padding: 16, marginTop: 12, background: 'white', borderRadius: 13, border: '1px solid #e9d5ff' }}>
                <div style={{ display: 'flex', gap: 7, marginBottom: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                  <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--txb)' }}>{h.name}</span>
                  <span style={{ fontSize: 11, padding: '2px 9px', borderRadius: 100, fontWeight: 700, background: conf.bg, color: conf.color }}>{h.confidence} confidence</span>
                  <span style={{ fontSize: 11, padding: '2px 9px', borderRadius: 100, fontWeight: 700, background: mag.bg, color: mag.color }}>{h.magnitude} impact</span>
                  <span style={{ fontSize: 11, color: 'var(--txm)' }}>{h.category}</span>
                </div>
                <p style={{ fontSize: 13, color: 'var(--tx)', lineHeight: 1.7 }}>{h.description}</p>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
