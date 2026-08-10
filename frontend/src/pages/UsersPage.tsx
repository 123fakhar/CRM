import { useEffect, useState, type FormEvent } from 'react'
import { getErrorMessage, usersApi } from '../services/api'
import type { User } from '../types'
import {
  Button,
  Card,
  EmptyState,
  Field,
  Input,
  Modal,
  PageHeader,
  Select,
  Toast,
  formatDate,
} from '../components/ui'

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    role: 'closer',
    agent_name: '',
    closer_name: '',
  })

  async function refresh() {
    setUsers(await usersApi.list())
  }

  useEffect(() => {
    void refresh().catch((err) => setError(getErrorMessage(err)))
  }, [])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    try {
      await usersApi.create({
        name: form.name,
        email: form.email,
        password: form.password,
        role: form.role,
        active: true,
        agent_name: form.role === 'agent' ? form.agent_name || form.name : null,
        closer_name: form.role === 'closer' ? form.closer_name || form.name : null,
      })
      setOpen(false)
      setForm({ name: '', email: '', password: '', role: 'closer', agent_name: '', closer_name: '' })
      setToast('User created.')
      await refresh()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div>
      <PageHeader
        title="Users"
        subtitle="Create accounts, assign roles, activate/deactivate, and reset passwords."
        actions={<Button onClick={() => setOpen(true)}>Create User</Button>}
      />
      {toast ? <Toast message={toast} onClose={() => setToast('')} /> : null}
      {error ? <p className="mb-4 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p> : null}

      {users.length === 0 ? (
        <EmptyState title="No users" />
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-sea-900 text-sea-50">
              <tr>
                {['Name', 'Email', 'Role', 'Profile', 'Status', 'Created', 'Actions'].map((h) => (
                  <th key={h} className="px-4 py-3">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-sea-900/10">
                  <td className="px-4 py-3 font-medium">{u.name}</td>
                  <td className="px-4 py-3">{u.email}</td>
                  <td className="px-4 py-3 capitalize">{u.role}</td>
                  <td className="px-4 py-3">{u.agent_name || u.closer_name || '—'}</td>
                  <td className="px-4 py-3">{u.active ? 'Active' : 'Inactive'}</td>
                  <td className="px-4 py-3">{formatDate(u.created_at)}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-2">
                      <Button
                        variant="secondary"
                        onClick={async () => {
                          await usersApi.update(u.id, { active: !u.active })
                          await refresh()
                        }}
                      >
                        {u.active ? 'Deactivate' : 'Activate'}
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={async () => {
                          const pw = prompt('Enter new password (min 8 characters)')
                          if (!pw) return
                          await usersApi.resetPassword(u.id, pw)
                          setToast('Password reset.')
                        }}
                      >
                        Reset Password
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      <Modal open={open} title="Create User" onClose={() => setOpen(false)}>
        <form onSubmit={onCreate} className="space-y-4">
          <Field label="Name">
            <Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Field>
          <Field label="Email">
            <Input
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </Field>
          <Field label="Password">
            <Input
              type="password"
              required
              minLength={8}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </Field>
          <Field label="Role">
            <Select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              <option value="admin">Admin</option>
              <option value="agent">Agent</option>
              <option value="closer">Closer</option>
            </Select>
          </Field>
          {form.role === 'agent' ? (
            <Field label="Agent Profile Name">
              <Input
                value={form.agent_name}
                placeholder="Defaults to user name"
                onChange={(e) => setForm({ ...form, agent_name: e.target.value })}
              />
            </Field>
          ) : null}
          {form.role === 'closer' ? (
            <Field label="Closer Profile Name">
              <Input
                value={form.closer_name}
                placeholder="Defaults to user name"
                onChange={(e) => setForm({ ...form, closer_name: e.target.value })}
              />
            </Field>
          ) : null}
          <Button type="submit">Create</Button>
        </form>
      </Modal>
    </div>
  )
}
