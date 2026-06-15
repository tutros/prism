import { Component, useState } from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { DecisionForm } from './features/comparison/DecisionForm'
import { ProgressView } from './features/progress/ProgressView'
import { ResultsDisplay } from './features/results/ResultsDisplay'
import { HistoryList } from './features/history/HistoryList'

class ErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: ReactNode }) {
    super(props)
    this.state = { hasError: false, error: null }
  }
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary:', error, info.componentStack)
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 32 }}>
          <div style={{ background: 'var(--sf)', padding: 24, borderRadius: 'var(--r)', border: '1px solid var(--bd)', maxWidth: 400 }}>
            <h2 style={{ color: '#dc2626', marginBottom: 8, fontWeight: 700 }}>Something went wrong</h2>
            <p style={{ color: 'var(--txm)', fontSize: 14, marginBottom: 16 }}>{this.state.error?.message}</p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              style={{ padding: '8px 20px', background: 'var(--ac)', color: '#fff', border: 'none', borderRadius: 10, cursor: 'pointer', fontWeight: 600, fontFamily: 'inherit' }}
            >
              Try Again
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

interface ActiveAnalysis {
  decisionId: string
  analysisId: string
}

function parseHash(): ActiveAnalysis | null {
  const hash = window.location.hash.slice(1)
  const parts = hash.split(':')
  if (parts.length === 2 && parts[0] && parts[1]) {
    return { decisionId: parts[0], analysisId: parts[1] }
  }
  return null
}

function App() {
  const [active, setActive] = useState<ActiveAnalysis | null>(() => parseHash())
  const [analysisStarted, setAnalysisStarted] = useState(false)
  const queryClient = useQueryClient()

  const handleAnalysisCreated = (decisionId: string, analysisId: string) => {
    const next = { decisionId, analysisId }
    setActive(next)
    setAnalysisStarted(true)
    window.location.hash = `${decisionId}:${analysisId}`
    queryClient.invalidateQueries({ queryKey: ['decisions'] })
  }

  const handleAnalysisComplete = () => {
    setAnalysisStarted(false)
  }

  const handleSelectHistory = (decisionId: string, analysisId: string) => {
    const next = { decisionId, analysisId }
    setActive(next)
    setAnalysisStarted(false)
    window.location.hash = `${decisionId}:${analysisId}`
  }

  const handleNew = () => {
    setActive(null)
    setAnalysisStarted(false)
    window.location.hash = ''
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', fontFamily: 'inherit' }}>
      {/* Nav */}
      <nav style={{
        background: 'var(--sf)', borderBottom: '1px solid var(--bd)', padding: '0 28px',
        height: 58, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        boxShadow: '0 1px 16px rgba(91,61,245,.07)', position: 'sticky', top: 0, zIndex: 10,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 34, height: 34, borderRadius: 11, background: 'var(--ac)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontSize: 18, fontWeight: 800,
          }}>⟁</div>
          <span style={{ fontSize: 19, fontWeight: 800, color: 'var(--txb)', letterSpacing: '-0.03em' }}>Prism</span>
        </div>
        {active && (
          <button
            onClick={handleNew}
            style={{
              fontSize: 13, fontWeight: 700, color: 'var(--ac)', background: 'var(--ac-dim)',
              border: 'none', padding: '8px 18px', borderRadius: 10, cursor: 'pointer', fontFamily: 'inherit',
            }}
          >
            + New
          </button>
        )}
      </nav>

      <div style={{ display: 'flex' }}>
        {/* Sidebar */}
        <aside style={{
          width: 256, flexShrink: 0, padding: '22px 16px', borderRight: '1px solid var(--bd)',
          background: 'var(--sf)', minHeight: 'calc(100vh - 58px)', position: 'sticky', top: 58,
          overflowY: 'auto', maxHeight: 'calc(100vh - 58px)',
        }}>
          <HistoryList
            activeDecisionId={active?.decisionId ?? null}
            onSelect={handleSelectHistory}
          />
        </aside>

        {/* Main */}
        <main style={{ flex: 1, padding: '32px 36px', maxWidth: 860 }}>
          {!active && (
            <DecisionForm onAnalysisCreated={handleAnalysisCreated} />
          )}
          {active && analysisStarted && (
            <ProgressView
              analysisId={active.analysisId}
              decisionId={active.decisionId}
              onComplete={handleAnalysisComplete}
            />
          )}
          {active && !analysisStarted && (
            <ResultsDisplay
              decisionId={active.decisionId}
              analysisId={active.analysisId}
            />
          )}
        </main>
      </div>
    </div>
  )
}

export default function AppWithErrorBoundary() {
  return (
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  )
}
