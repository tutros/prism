import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { ComparisonForm } from './features/comparison/ComparisonForm'
import { ResultsDisplay } from './features/results/ResultsDisplay'
import { HistoryList } from './features/history/HistoryList'
import { useResults } from './features/results/useResults'

function App() {
  const [comparisonId, setComparisonId] = useState<string | null>(null)
  const [formKey, setFormKey] = useState(0)
  const queryClient = useQueryClient()
  const { data: result } = useResults(comparisonId)

  const handleNewComparison = (id: string) => {
    setComparisonId(id)
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

            {comparisonId && result && (
              <section className="bg-white p-4 sm:p-6 rounded-lg shadow">
                <h2 className="text-xl font-semibold mb-4">Results</h2>
                <ResultsDisplay result={result} />
              </section>
            )}
          </main>
        </div>
      </div>
    </div>
  )
}

export default App
