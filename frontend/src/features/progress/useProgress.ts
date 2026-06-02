import { useEffect, useState, useCallback } from 'react'
import { API_BASE } from '../../lib/api'

export function useProgress(analysisId: string | null) {
  const [messages, setMessages] = useState<string[]>([])

  const reset = useCallback(() => setMessages([]), [])

  useEffect(() => {
    if (!analysisId) return
    reset()

    const es = new EventSource(`${API_BASE}/api/progress/${analysisId}`)

    es.addEventListener('progress', (event) => {
      try {
        const data = JSON.parse((event as MessageEvent).data)
        if (data.status) setMessages(prev => [...prev, data.status])
      } catch { /* ignore */ }
    })

    es.addEventListener('complete', () => es.close())

    es.addEventListener('error', () => es.close())

    es.onerror = () => es.close()

    return () => es.close()
  }, [analysisId, reset])

  return { messages }
}
