import { useState } from 'react'
import { ComparisonForm } from './features/comparison/ComparisonForm'
import { ResultsDisplay } from './features/results/ResultsDisplay'
import { useResults } from './features/results/useResults'

function App() {
  const [comparisonId, setComparisonId] = useState<string | null>(null)
  const { data: result } = useResults(comparisonId)

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Hidden Cost Comparator
          </h1>
          <p className="text-gray-600">
            Compare options by surfacing hidden costs and systemic impacts.
          </p>
        </header>

        <main className="space-y-8">
          <section className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Compare Options</h2>
            <ComparisonForm onSubmit={setComparisonId} />
          </section>

          {comparisonId && result && (
            <section className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">Results</h2>
              <ResultsDisplay result={result} />
            </section>
          )}
        </main>
      </div>
    </div>
  )
}

export default App
