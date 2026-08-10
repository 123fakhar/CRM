import { useEffect, useState, type FormEvent } from 'react'
import { agentsApi, campaignsApi, getErrorMessage, leadsApi, settingsApi } from '../services/api'
import type { Agent, Campaign, AppSettings } from '../types'
import { useAuth } from '../context/AuthContext'
import { Button, Card, Field, Input, PageHeader, Select, TextArea, Toast } from '../components/ui'

export default function SalesFormPage() {
  const { user } = useAuth()
  const [agents, setAgents] = useState<Agent[]>([])
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [settings, setSettings] = useState<AppSettings | null>(null)
  const [toast, setToast] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState({
    customer_number: '',
    first_name: '',
    last_name: '',
    state: '',
    zip_code: '',
    agent_id: '',
    campaign_id: '',
    did: '',
    d1: '',
    other: '',
    comments: '',
  })

  useEffect(() => {
    void Promise.all([agentsApi.list(true), campaignsApi.list(true), settingsApi.get()]).then(
      ([a, c, s]) => {
        setAgents(a)
        setCampaigns(c)
        setSettings(s)
      },
    )
  }, [])

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await leadsApi.create({
        customer_number: form.customer_number,
        first_name: form.first_name,
        last_name: form.last_name,
        state: form.state,
        zip_code: form.zip_code,
        agent_id: Number(form.agent_id),
        campaign_id: Number(form.campaign_id),
        did: form.did,
        d1: form.d1 || null,
        other: form.other || null,
        comments: form.comments || null,
      })
      setToast('Sales form submitted successfully.')
      setForm({
        customer_number: '',
        first_name: '',
        last_name: '',
        state: '',
        zip_code: '',
        agent_id: '',
        campaign_id: '',
        did: '',
        d1: '',
        other: '',
        comments: '',
      })
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Seagulls Communications Inhouse Sales Sheet"
        subtitle="Submit a new lead. Status fields are set automatically to Pending and locked after submission."
      />
      {toast ? <Toast message={toast} onClose={() => setToast('')} /> : null}
      <Card className="max-w-4xl">
        <form onSubmit={onSubmit} className="space-y-8">
          <section>
            <h2 className="mb-4 font-display text-2xl">Customer Information</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Customer Number *">
                <Input required value={form.customer_number} onChange={(e) => update('customer_number', e.target.value)} />
              </Field>
              <Field label="First Name *">
                <Input required value={form.first_name} onChange={(e) => update('first_name', e.target.value)} />
              </Field>
              <Field label="Last Name *">
                <Input required value={form.last_name} onChange={(e) => update('last_name', e.target.value)} />
              </Field>
              <Field label="State *">
                <Select required value={form.state} onChange={(e) => update('state', e.target.value)}>
                  <option value="">Select state</option>
                  {(settings?.us_states || []).map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="ZipCode *">
                <Input
                  required
                  pattern="\d{5}(-\d{4})?"
                  title="5 digits or ZIP+4"
                  value={form.zip_code}
                  onChange={(e) => update('zip_code', e.target.value)}
                />
              </Field>
            </div>
          </section>

          <section>
            <h2 className="mb-4 font-display text-2xl">Employee Information</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Agent Name *">
                <Select required value={form.agent_id} onChange={(e) => update('agent_id', e.target.value)}>
                  <option value="">Select agent</option>
                  {agents.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Closer Name">
                <Input
                  readOnly
                  value={user?.closer_name || user?.name || ''}
                  className="bg-sea-50 text-sea-800"
                />
              </Field>
            </div>
          </section>

          <section>
            <h2 className="mb-4 font-display text-2xl">Campaign Information</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Campaign Name *">
                <Select required value={form.campaign_id} onChange={(e) => update('campaign_id', e.target.value)}>
                  <option value="">Select campaign</option>
                  {campaigns.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="DID *">
                <Input required value={form.did} onChange={(e) => update('did', e.target.value)} />
              </Field>
            </div>
          </section>

          <section>
            <h2 className="mb-4 font-display text-2xl">Additional Information</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="D1">
                <Input value={form.d1} onChange={(e) => update('d1', e.target.value)} />
              </Field>
              <Field label="Other">
                <Input value={form.other} onChange={(e) => update('other', e.target.value)} />
              </Field>
              <div className="sm:col-span-2">
                <Field label="Comments">
                  <TextArea rows={4} value={form.comments} onChange={(e) => update('comments', e.target.value)} />
                </Field>
              </div>
            </div>
          </section>

          {error ? <p className="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p> : null}

          <Button type="submit" disabled={submitting || !user?.closer_id}>
            {submitting ? 'Submitting…' : 'Submit Sales Form'}
          </Button>
          {!user?.closer_id ? (
            <p className="text-sm text-amber-800">
              A Closer profile is required to submit forms. Use a Closer account (or link a closer profile).
            </p>
          ) : null}
        </form>
      </Card>
    </div>
  )
}
