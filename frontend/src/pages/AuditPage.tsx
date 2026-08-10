import { useEffect, useState } from 'react'
import { auditApi, getErrorMessage } from '../services/api'
import type { AuditEntry } from '../types'
import { Button, Card, EmptyState, Field, Input, LoadingBlock, PageHeader, formatDate } from '../components/ui'

export default function AuditPage() {
  const [items, setItems] = useState<AuditEntry[]>([])
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(0)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      try {
        const res = await auditApi.list({ page, page_size: 50, search })
        if (!cancelled) {
          setItems(res.items)
          setPages(res.pages)
        }
      } catch (err) {
        if (!cancelled) setError(getErrorMessage(err))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [page, search])

  return (
    <div>
      <PageHeader title="Audit Log" subtitle="Every important modification is recorded. Read-only." />
      {error ? <p className="mb-4 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p> : null}
      <Card className="mb-4">
        <Field label="Search">
          <Input
            placeholder="User, action, entity id, values…"
            value={search}
            onChange={(e) => {
              setPage(1)
              setSearch(e.target.value)
            }}
          />
        </Field>
      </Card>
      {loading ? (
        <LoadingBlock />
      ) : items.length === 0 ? (
        <EmptyState title="No audit entries" />
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-sea-900 text-sea-50">
              <tr>
                {['Time', 'User', 'Role', 'Action', 'Entity', 'Entity ID', 'Old', 'New'].map((h) => (
                  <th key={h} className="px-3 py-3">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-t border-sea-900/10 align-top">
                  <td className="px-3 py-3 whitespace-nowrap">{formatDate(item.timestamp)}</td>
                  <td className="px-3 py-3">{item.user_name}</td>
                  <td className="px-3 py-3 capitalize">{item.role}</td>
                  <td className="px-3 py-3">{item.action}</td>
                  <td className="px-3 py-3">{item.entity}</td>
                  <td className="px-3 py-3">{item.entity_id || '—'}</td>
                  <td className="px-3 py-3 max-w-[180px] break-words text-sea-800/80">{item.old_value || '—'}</td>
                  <td className="px-3 py-3 max-w-[180px] break-words text-sea-800/80">{item.new_value || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
      {pages > 1 ? (
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </Button>
          <Button variant="secondary" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>
            Next
          </Button>
        </div>
      ) : null}
    </div>
  )
}
