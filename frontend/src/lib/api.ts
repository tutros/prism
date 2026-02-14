const API_BASE = 'http://localhost:8000'

export async function apiPost<T>(endpoint: string, data: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    let message = `API error: ${res.status}`
    try {
      const body = await res.json()
      if (body.detail) {
        message = body.detail
      }
    } catch {
      // Response body not parseable as JSON, use status code fallback
    }
    throw new Error(message)
  }
  return res.json()
}

export async function apiGet<T>(endpoint: string): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`)
  if (!res.ok) {
    if (res.status === 404) {
      throw new Error('Not found')
    }
    throw new Error(`API error: ${res.status}`)
  }
  return res.json()
}
