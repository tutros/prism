import { useEffect, useState, useCallback } from 'react'

interface ProgressState {
  status: string
  error: string | null
  complete: boolean
  connected: boolean
}

export function useProgress(comparisonId: string | null) {
  const [state, setState] = useState<ProgressState>({
    status: 'Initializing...',
    error: null,
    complete: false,
    connected: false,
  })

  const resetProgress = useCallback(() => {
    setState({
      status: 'Initializing...',
      error: null,
      complete: false,
      connected: false,
    })
  }, [])

  useEffect(() => {
    if (!comparisonId) return

    // Reset state for new comparison
    resetProgress()

    const eventSource = new EventSource(`/api/progress/${comparisonId}`)

    eventSource.onopen = () => {
      setState(prev => ({ ...prev, connected: true }))
    }

    eventSource.addEventListener('progress', (event) => {
      try {
        const data = JSON.parse(event.data)
        setState(prev => ({ ...prev, status: data.status }))
      } catch (e) {
        console.error('Failed to parse progress event:', e)
      }
    })

    eventSource.addEventListener('complete', () => {
      setState(prev => ({ ...prev, complete: true, status: 'Complete' }))
      eventSource.close()
    })

    eventSource.addEventListener('error', (event) => {
      // Check if it's a custom error event with data
      if (event instanceof MessageEvent && event.data) {
        try {
          const data = JSON.parse(event.data)
          setState(prev => ({ ...prev, error: data.error }))
        } catch (e) {
          setState(prev => ({ ...prev, error: 'Connection error' }))
        }
      }
      eventSource.close()
    })

    eventSource.onerror = () => {
      // Connection error - EventSource will auto-reconnect by default
      // After 3 failed reconnects, give up
      setState(prev => {
        if (!prev.connected) {
          // Never connected - fall back to polling
          return { ...prev, error: 'Unable to connect to progress stream' }
        }
        return prev
      })
    }

    return () => {
      eventSource.close()
    }
  }, [comparisonId, resetProgress])

  return state
}
