interface ProgressDisplayProps {
  status: string
  connected: boolean
}

export function ProgressDisplay({ status, connected }: ProgressDisplayProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 space-y-4">
      {/* Spinner */}
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />

      {/* Status text */}
      <div className="text-center">
        <p className="text-gray-700 font-medium">{status}</p>
        {!connected && (
          <p className="text-xs text-gray-500 mt-1">Connecting...</p>
        )}
      </div>

      {/* Progress stages indicator */}
      <div className="flex items-center space-x-2 text-xs text-gray-400">
        <StageIndicator active={status.includes('Searching')} label="Search" />
        <span>-</span>
        <StageIndicator active={status.includes('Analyzing') || status.includes('Found')} label="Analyze" />
        <span>-</span>
        <StageIndicator active={status.includes('Generated') || status.includes('Finalizing')} label="Generate" />
      </div>
    </div>
  )
}

function StageIndicator({ active, label }: { active: boolean; label: string }) {
  return (
    <span className={active ? 'text-blue-600 font-medium' : ''}>
      {label}
    </span>
  )
}
