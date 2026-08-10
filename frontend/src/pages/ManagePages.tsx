import { useEffect, useState, type FormEvent } from 'react'
import { agentsApi, closersApi, campaignsApi, getErrorMessage } from '../services/api'
import { Button, Card, EmptyState, Field, Input, PageHeader, Toast, formatDate } from '../components/ui'

type Entity = { id: number; name: string; active: boolean; created_at: string }

function EntityManager({
  title,
  subtitle,
  list,
  create,
  update,
  remove,
}: {
  title: string
  subtitle: string
  list: () => Promise<Entity[]>
  create: (payload: { name: string; active?: boolean }) => Promise<Entity>
  update: (id: number, payload: Partial<Entity>) => Promise<Entity>
  remove: (id: number) => Promise<{ message: string }>
}) {
  const [items, setItems] = useState<Entity[]>([])
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')

  async function refresh() {
    setItems(await list())
  }

  useEffect(() => {
    void refresh().catch((err) => setError(getErrorMessage(err)))
  }, [])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    try {
      await create({ name, active: true })
      setName('')
      setToast(`${title.slice(0, -1)} created.`)
      await refresh()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div>
      <PageHeader title={title} subtitle={subtitle} />
      {toast ? <Toast message={toast} onClose={() => setToast('')} /> : null}
      {error ? <p className="mb-4 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p> : null}

      <Card className="mb-4">
        <form onSubmit={onCreate} className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1">
            <Field label={`New ${title.slice(0, -1)} Name`}>
              <Input required value={name} onChange={(e) => setName(e.target.value)} />
            </Field>
          </div>
          <Button type="submit">Add</Button>
        </form>
      </Card>

      {items.length === 0 ? (
        <EmptyState title={`No ${title.toLowerCase()} yet`} description="Add the first record above." />
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-sea-900 text-sea-50">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Created</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-t border-sea-900/10">
                  <td className="px-4 py-3 font-medium">{item.name}</td>
                  <td className="px-4 py-3">{item.active ? 'Active' : 'Inactive'}</td>
                  <td className="px-4 py-3">{formatDate(item.created_at)}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-2">
                      <Button
                        variant="secondary"
                        onClick={async () => {
                          await update(item.id, { active: !item.active })
                          await refresh()
                        }}
                      >
                        {item.active ? 'Deactivate' : 'Activate'}
                      </Button>
                      <Button
                        variant="danger"
                        onClick={async () => {
                          if (!confirm(`Delete or deactivate ${item.name}?`)) return
                          const res = await remove(item.id)
                          setToast(res.message)
                          await refresh()
                        }}
                      >
                        Delete
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  )
}

export function AgentsPage() {
  return (
    <EntityManager
      title="Agents"
      subtitle="Manage agent directory used on the sales form."
      list={agentsApi.list}
      create={agentsApi.create}
      update={agentsApi.update}
      remove={agentsApi.remove}
    />
  )
}

export function ClosersPage() {
  return (
    <EntityManager
      title="Closers"
      subtitle="Manage closer directory and associations."
      list={closersApi.list}
      create={closersApi.create}
      update={closersApi.update}
      remove={closersApi.remove}
    />
  )
}

export function CampaignsPage() {
  return (
    <EntityManager
      title="Campaigns"
      subtitle="Manage campaign names available on the sales form."
      list={campaignsApi.list}
      create={campaignsApi.create}
      update={campaignsApi.update}
      remove={campaignsApi.remove}
    />
  )
}
