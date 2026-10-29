import { useEffect, useState } from 'react'
import { API_BASE } from '../../lib/api'

const NO_MESSAGES: string[] = []

export function useProgress(analysisId: string | null) {
  // Messages are tagged with the analysis they belong to, so a new analysisId
  // reads as empty without resetting state from inside the effect.
  const [stream, setStream] = useState<{ id: string; messages: string[] } | null>(null)

  useEffect(() => {
    if (!analysisId) return

    const es = new EventSource(`${API_BASE}/api/progress/${analysisId}`)

    es.addEventListener('progress', (event) => {
      try {
        const data = JSON.parse((event as MessageEvent).data)
        if (data.status) {
          setStream(prev =>
            prev?.id === analysisId
              ? { id: analysisId, messages: [...prev.messages, data.status] }
              : { id: analysisId, messages: [data.status] }
          )
        }
      } catch { /* ignore */ }
    })

    es.addEventListener('complete', () => es.close())

    es.addEventListener('error', () => es.close())

    es.onerror = () => es.close()

    return () => es.close()
  }, [analysisId])

  const messages = stream?.id === analysisId ? stream.messages : NO_MESSAGES
  return { messages }
}
