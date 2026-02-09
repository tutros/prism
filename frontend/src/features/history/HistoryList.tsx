import { useHistory } from './useHistory'

interface HistoryListProps {
  onSelect: (comparisonId: string) => void
  currentId: string | null
}

export function HistoryList({ onSelect, currentId }: HistoryListProps) {
  const { data, isLoading, error } = useHistory()

  if (isLoading) {
    return (
      <div className="text-sm text-gray-500">Loading history...</div>
    )
  }

  if (error) {
    return (
      <div className="text-sm text-red-600">Failed to load history</div>
    )
  }

  const comparisons = data?.comparisons ?? []

  if (comparisons.length === 0) {
    return (
      <div className="text-sm text-gray-500">No previous comparisons</div>
    )
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="space-y-2">
      {comparisons.map((comparison) => (
        <button
          key={comparison.comparison_id}
          onClick={() => onSelect(comparison.comparison_id)}
          className={`w-full text-left p-3 rounded-lg border transition-colors ${
            currentId === comparison.comparison_id
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 bg-white hover:bg-gray-50'
          }`}
        >
          <div className="flex justify-between items-start">
            <div className="min-w-0 flex-1">
              <p className="font-medium text-gray-900 truncate">
                {comparison.option_a_name} vs {comparison.option_b_name}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {formatDate(comparison.created_at)}
              </p>
            </div>
            <span className={`ml-2 px-2 py-0.5 text-xs rounded ${
              currentId === comparison.comparison_id && comparison.status === 'completed'
                ? 'bg-blue-100 text-blue-700'
                : comparison.status === 'completed'
                ? 'bg-green-100 text-green-700'
                : comparison.status === 'processing'
                ? 'bg-yellow-100 text-yellow-700'
                : 'bg-red-100 text-red-700'
            }`}>
              {currentId === comparison.comparison_id && comparison.status === 'completed'
                ? 'reviewing'
                : comparison.status}
            </span>
          </div>
        </button>
      ))}
    </div>
  )
}
