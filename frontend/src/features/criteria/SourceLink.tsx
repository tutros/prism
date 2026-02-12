import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { SourceMetadata } from '../comparison/types'

const API_BASE = 'http://localhost:8000'

// Quality badge styling - matches existing badge patterns
const QUALITY_BADGE_MAP: Record<string, { label: string | null; classes: string }> = {
  'peer-reviewed': { label: 'Peer', classes: 'bg-green-100 text-green-700' },
  'government': { label: 'Gov', classes: 'bg-blue-100 text-blue-700' },
  'industry': { label: 'Ind', classes: 'bg-purple-100 text-purple-700' },
  'news': { label: 'News', classes: 'bg-gray-100 text-gray-600' },
  'blog': { label: 'Blog', classes: 'bg-yellow-100 text-yellow-700' },
  'unknown': { label: null, classes: '' },
}

interface SourceLinkProps {
  url: string
  metadata?: SourceMetadata
  comparisonId: string
}

export function SourceLink({ url, metadata, comparisonId }: SourceLinkProps) {
  const queryClient = useQueryClient()

  // Extract domain name from URL
  let domain: string
  try {
    domain = new URL(url).hostname.replace('www.', '')
  } catch {
    domain = url.slice(0, 30) + '...'
  }

  const flagged = metadata?.flagged ?? false
  const quality = metadata?.quality ?? 'unknown'
  const lastVerified = metadata?.last_verified
  const badge = QUALITY_BADGE_MAP[quality] ?? QUALITY_BADGE_MAP['unknown']

  // Format last_verified for tooltip
  const lastVerifiedText = lastVerified
    ? `Last verified: ${new Date(lastVerified).toLocaleDateString()}`
    : 'Verification date unknown'

  const flagMutation = useMutation({
    mutationFn: async ({ flagged }: { flagged: boolean }) => {
      const res = await fetch(
        `${API_BASE}/api/comparisons/${comparisonId}/sources/flag`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url, flagged }),
        }
      )
      if (!res.ok) throw new Error('Flag update failed')
      return res.json()
    },
    onMutate: async ({ flagged }) => {
      await queryClient.cancelQueries({ queryKey: ['comparison', comparisonId] })
      const previous = queryClient.getQueryData(['comparison', comparisonId])

      queryClient.setQueryData(['comparison', comparisonId], (old: any) => {
        if (!old) return old
        return {
          ...old,
          source_metadata: {
            ...old.source_metadata,
            [url]: { ...(old.source_metadata?.[url] ?? { quality: 'unknown' }), flagged },
          },
        }
      })

      return { previous }
    },
    onError: (_err, _vars, context) => {
      queryClient.setQueryData(['comparison', comparisonId], context?.previous)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['comparison', comparisonId] })
    },
  })

  const handleFlagClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    flagMutation.mutate({ flagged: !flagged })
  }

  return (
    <span
      className={`inline-flex items-center gap-1 ${flagged ? 'opacity-50' : ''}`}
      title={lastVerifiedText}
    >
      {badge?.label && (
        <span className={`px-1 py-0.5 text-xs rounded ${badge.classes}`}>
          {badge.label}
        </span>
      )}
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className={`text-xs text-blue-600 hover:underline ${flagged ? 'line-through' : ''}`}
        onClick={(e) => e.stopPropagation()}
      >
        {domain}
      </a>
      <button
        onClick={handleFlagClick}
        disabled={flagMutation.isPending}
        className={`text-xs px-0.5 ${flagged ? 'text-red-500' : 'text-gray-300 hover:text-gray-500'} disabled:opacity-50`}
        title={flagged ? 'Remove flag' : 'Flag as unreliable'}
      >
        {'\u2691'}
      </button>
    </span>
  )
}
