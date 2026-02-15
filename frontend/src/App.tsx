import { Component, useState, useEffect } from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { ComparisonForm } from './features/comparison/ComparisonForm'
import { ResultsDisplay } from './features/results/ResultsDisplay'
import { HistoryList } from './features/history/HistoryList'
import { useResults } from './features/results/useResults'

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
    console.error('ErrorBoundary caught:', error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
          <div className="bg-white p-6 rounded-lg shadow max-w-md">
            <h2 className="text-lg font-semibold text-red-700 mb-2">Something went wrong</h2>
            <p className="text-sm text-gray-600 mb-4">{this.state.error?.message}</p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
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

function App() {
  // Restore comparisonId from URL hash on mount (survives browser refresh)
  const [comparisonId, setComparisonId] = useState<string | null>(() => {
    const hash = window.location.hash.slice(1)
    return hash || null
  })
  const [formKey, setFormKey] = useState(0)
  const queryClient = useQueryClient()
  const { data: result } = useResults(comparisonId)

  // Sync comparisonId to URL hash
  useEffect(() => {
    window.location.hash = comparisonId ?? ''
  }, [comparisonId])

  const handleNewComparison = (id: string) => {
    setComparisonId(id)
    // Invalidate comparison data (dedup may return same id with updated fields)
    queryClient.invalidateQueries({ queryKey: ['comparison', id] })
    // Invalidate history to include new comparison
    queryClient.invalidateQueries({ queryKey: ['history'] })
  }

  const handleSelectHistory = (id: string) => {
    setComparisonId(id)
  }

  const handleNewComparisonClick = () => {
    setComparisonId(null)
    setFormKey((k) => k + 1) // Force form reset
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <header className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
                Hidden Cost Comparator
              </h1>
              <p className="text-gray-600 text-sm sm:text-base">
                Compare options by surfacing hidden costs and systemic impacts.
              </p>
            </div>
            {comparisonId && (
              <button
                onClick={handleNewComparisonClick}
                className="self-start px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
              >
                New Comparison
              </button>
            )}
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar - History */}
          <aside className="lg:col-span-1 order-2 lg:order-1">
            <div className="bg-white p-4 rounded-lg shadow">
              <h2 className="text-lg font-semibold mb-4">History</h2>
              <HistoryList
                onSelect={handleSelectHistory}
                currentId={comparisonId}
              />
            </div>
          </aside>

          {/* Main Content */}
          <main className="lg:col-span-3 space-y-8 order-1 lg:order-2">
            {!comparisonId && (
              <section className="bg-white p-4 sm:p-6 rounded-lg shadow">
                <h2 className="text-xl font-semibold mb-4">Compare Options</h2>
                <ComparisonForm
                  key={formKey}
                  onSubmit={handleNewComparison}
                />
              </section>
            )}

            {comparisonId && !result && (
              <section className="bg-white p-4 sm:p-6 rounded-lg shadow">
                <div className="flex items-center gap-3 text-gray-600">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Loading comparison...
                </div>
              </section>
            )}

            {comparisonId && result && (
              <section className="bg-white p-4 sm:p-6 rounded-lg shadow">
                <h2 className="text-xl font-semibold mb-4">Results</h2>
                <ResultsDisplay result={result} comparisonId={comparisonId} onNewComparison={handleNewComparison} />
              </section>
            )}
          </main>
        </div>
      </div>
    </div>
  )
}

function AppWithErrorBoundary() {
  return (
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  )
}

export default AppWithErrorBoundary
