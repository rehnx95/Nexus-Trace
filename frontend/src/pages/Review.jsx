import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../api'
import Panel from '../components/Panel'

export default function Review() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['review-merges'],
    queryFn: api.listMergeCandidates,
  })
  const decide = useMutation({
    mutationFn: ({ left, right, status }) => api.decideMerge(left, right, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['review-merges'] }),
  })
  const items = data?.items || []

  return (
    <Panel title="Merge Review Queue" hint="Review uncertain entity resolution decisions.">
      {isLoading && <div className="text-sm text-light-muted dark:text-muted">Loading candidates…</div>}
      {!isLoading && items.length === 0 && (
        <div className="text-sm text-light-muted dark:text-muted">No merge candidates pending review.</div>
      )}
      <div className="space-y-3">
        {items.map((item) => (
          <div key={`${item.left}-${item.right}`} className="border border-light-border dark:border-border rounded-lg p-4">
            <div className="font-mono text-sm">{item.left} ↔ {item.right}</div>
            <div className="text-xs text-light-muted dark:text-muted mt-1">
              Score: {item.score.toFixed(1)}% · {item.reasons.join(', ') || 'No reasons recorded'}
            </div>
            <div className="flex gap-2 mt-3">
              <button
                disabled={decide.isPending}
                onClick={() => decide.mutate({ left: item.left, right: item.right, status: 'approved' })}
                className="px-3 py-1.5 text-xs border border-success text-success rounded-lg"
              >
                Approve
              </button>
              <button
                disabled={decide.isPending}
                onClick={() => decide.mutate({ left: item.left, right: item.right, status: 'rejected' })}
                className="px-3 py-1.5 text-xs border border-danger text-danger rounded-lg"
              >
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  )
}
