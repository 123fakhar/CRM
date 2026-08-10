import { useEffect, useMemo, useState } from 'react'
import {
  agentsApi,
  campaignsApi,
  closersApi,
  getErrorMessage,
  leadsApi,
  settingsApi,
} from '../services/api'
import type { Agent, AppSettings, Campaign, Closer, Lead, LeadFilters } from '../types'
import { useAuth } from '../context/AuthContext'
import {
  Button,
  Card,
  EmptyState,
  Field,
  Input,
  LoadingBlock,
  Modal,
  PageHeader,
  Select,
  StatusBadge,
  TextArea,
  Toast,
  formatDate,
} from '../components/ui'

export default function LeadsPage({ title = 'Leads' }: { title?: string }) {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const [leads, setLeads] = useState<Lead[]>([])
  const [total, setTotal] = useState(0)
  const [pages, setPages] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')
  const [modalError, setModalError] = useState('')
  const [agents, setAgents] = useState<Agent[]>([])
  const [closers, setClosers] = useState<Closer[]>([])
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [settings, setSettings] = useState<AppSettings | null>(null)
  const [selected, setSelected] = useState<Lead | null>(null)
  const [edit, setEdit] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)
  const [filters, setFilters] = useState<LeadFilters>({
    search: '',
    date_preset: '',
  })

  const query = useMemo(
    () => ({
      ...filters,
      page,
      page_size: 25,
    }),
    [filters, page],
  )

  async function load() {
    setLoading(true)
    setError('')
    try {
      const res = await leadsApi.list(query)
      setLeads(res.items)
      setTotal(res.total)
      setPages(res.pages)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [query])

  useEffect(() => {
    void Promise.all([
      agentsApi.list(),
      closersApi.list(),
      campaignsApi.list(),
      settingsApi.get(),
    ]).then(([a, c, camp, s]) => {
      setAgents(a)
      setClosers(c)
      setCampaigns(camp)
      setSettings(s)
    })
  }, [])

  function openLead(lead: Lead) {
    setModalError('')
    setSelected(lead)
    applyLeadToEdit(lead)
  }

  function applyLeadToEdit(lead: Lead) {
    setEdit({
      customer_number: lead.customer_number,
      first_name: lead.first_name,
      last_name: lead.last_name,
      state: lead.state,
      zip_code: lead.zip_code,
      agent_id: String(lead.agent_id),
      closer_id: String(lead.closer_id),
      campaign_id: String(lead.campaign_id),
      did: lead.did,
      d1: lead.d1 || '',
      other: lead.other || '',
      comments: lead.comments || '',
      buyer_response: lead.buyer_response,
      final_status: lead.final_status,
      rejection_reason: lead.rejection_reason || '',
      admin_notes: lead.admin_notes || '',
    })
  }

  async function saveLead() {
    if (!selected || !isAdmin) return
    setModalError('')
    setError('')

    if (edit.final_status === 'Rejected' && !edit.rejection_reason.trim()) {
      setModalError('Rejected leads require a rejection reason.')
      return
    }

    setSaving(true)
    try {
      const payload: Record<string, unknown> = {
        customer_number: edit.customer_number,
        first_name: edit.first_name,
        last_name: edit.last_name,
        state: edit.state,
        zip_code: edit.zip_code,
        agent_id: Number(edit.agent_id),
        closer_id: Number(edit.closer_id),
        campaign_id: Number(edit.campaign_id),
        did: edit.did,
        d1: edit.d1 || null,
        other: edit.other || null,
        comments: edit.comments || null,
        buyer_response: edit.buyer_response,
        final_status: edit.final_status,
        rejection_reason: edit.final_status === 'Rejected' ? edit.rejection_reason.trim() : null,
        admin_notes: edit.admin_notes || null,
      }
      const updated = await leadsApi.update(selected.id, payload)
      setSelected(updated)
      applyLeadToEdit(updated)
      setToast('Lead updated successfully.')
      await load()
    } catch (err) {
      const message = getErrorMessage(err)
      setModalError(message)
      setError(message)
    } finally {
      setSaving(false)
    }
  }

  async function removeLead() {
    if (!selected || !isAdmin) return
    if (!confirm(`Delete Lead #${selected.lead_number}? This cannot be undone.`)) return
    try {
      await leadsApi.remove(selected.id)
      setSelected(null)
      setToast('Lead deleted.')
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div>
      <PageHeader title={title} subtitle={`${total} lead${total === 1 ? '' : 's'} found`} />
      {toast ? <Toast message={toast} onClose={() => setToast('')} /> : null}
      {error ? <p className="mb-4 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p> : null}

      <Card className="mb-4">
        <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-4">
          <Field label="Search">
            <Input
              placeholder="Lead ID, customer, name, agent, closer"
              value={filters.search || ''}
              onChange={(e) => {
                setPage(1)
                setFilters((f) => ({ ...f, search: e.target.value }))
              }}
            />
          </Field>
          {isAdmin ? (
            <>
              <Field label="Agent">
                <Select
                  value={filters.agent_id || ''}
                  onChange={(e) => {
                    setPage(1)
                    setFilters((f) => ({ ...f, agent_id: e.target.value ? Number(e.target.value) : undefined }))
                  }}
                >
                  <option value="">All</option>
                  {agents.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Closer">
                <Select
                  value={filters.closer_id || ''}
                  onChange={(e) => {
                    setPage(1)
                    setFilters((f) => ({ ...f, closer_id: e.target.value ? Number(e.target.value) : undefined }))
                  }}
                >
                  <option value="">All</option>
                  {closers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </Select>
              </Field>
            </>
          ) : null}
          <Field label="Campaign">
            <Select
              value={filters.campaign_id || ''}
              onChange={(e) => {
                setPage(1)
                setFilters((f) => ({ ...f, campaign_id: e.target.value ? Number(e.target.value) : undefined }))
              }}
            >
              <option value="">All</option>
              {campaigns.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Final Status">
            <Select
              value={filters.final_status || ''}
              onChange={(e) => {
                setPage(1)
                setFilters((f) => ({ ...f, final_status: e.target.value || undefined }))
              }}
            >
              <option value="">All</option>
              {(settings?.final_statuses || ['Pending', 'Accepted', 'Rejected']).map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Buyer Response">
            <Select
              value={filters.buyer_response || ''}
              onChange={(e) => {
                setPage(1)
                setFilters((f) => ({ ...f, buyer_response: e.target.value || undefined }))
              }}
            >
              <option value="">All</option>
              {(settings?.buyer_responses || []).map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="State">
            <Select
              value={filters.state || ''}
              onChange={(e) => {
                setPage(1)
                setFilters((f) => ({ ...f, state: e.target.value || undefined }))
              }}
            >
              <option value="">All</option>
              {(settings?.us_states || []).map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Date Range">
            <Select
              value={filters.date_preset || ''}
              onChange={(e) => {
                setPage(1)
                setFilters((f) => ({ ...f, date_preset: e.target.value || undefined }))
              }}
            >
              <option value="">All time</option>
              <option value="today">Today</option>
              <option value="yesterday">Yesterday</option>
              <option value="this_week">This Week</option>
              <option value="this_month">This Month</option>
              <option value="last_month">Last Month</option>
              <option value="custom">Custom</option>
            </Select>
          </Field>
          {filters.date_preset === 'custom' ? (
            <>
              <Field label="From">
                <Input
                  type="date"
                  value={filters.date_from?.slice(0, 10) || ''}
                  onChange={(e) =>
                    setFilters((f) => ({ ...f, date_from: e.target.value ? `${e.target.value}T00:00:00Z` : undefined }))
                  }
                />
              </Field>
              <Field label="To">
                <Input
                  type="date"
                  value={filters.date_to?.slice(0, 10) || ''}
                  onChange={(e) =>
                    setFilters((f) => ({ ...f, date_to: e.target.value ? `${e.target.value}T00:00:00Z` : undefined }))
                  }
                />
              </Field>
            </>
          ) : null}
        </div>
      </Card>

      {loading ? (
        <LoadingBlock />
      ) : leads.length === 0 ? (
        <EmptyState title="No leads found" description="Try adjusting filters or submit a new sales form." />
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-sea-900 text-sea-50">
              <tr>
                {[
                  'Lead ID',
                  'Customer #',
                  'Customer Name',
                  'Agent',
                  'Closer',
                  'Campaign',
                  'Initial',
                  'Buyer Response',
                  'Final',
                  'Submitted',
                  'Updated',
                ].map((h) => (
                  <th key={h} className="px-3 py-3 font-semibold">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {leads.map((lead) => (
                <tr
                  key={lead.id}
                  onClick={() => openLead(lead)}
                  className="cursor-pointer border-t border-sea-900/10 hover:bg-sea-50"
                >
                  <td className="px-3 py-3 font-semibold">#{lead.lead_number}</td>
                  <td className="px-3 py-3">{lead.customer_number}</td>
                  <td className="px-3 py-3">
                    {lead.first_name} {lead.last_name}
                  </td>
                  <td className="px-3 py-3">{lead.agent_name}</td>
                  <td className="px-3 py-3">{lead.closer_name}</td>
                  <td className="px-3 py-3">{lead.campaign_name}</td>
                  <td className="px-3 py-3">
                    <StatusBadge status={lead.initial_status} />
                  </td>
                  <td className="px-3 py-3">
                    <StatusBadge status={lead.buyer_response} />
                  </td>
                  <td className="px-3 py-3">
                    <StatusBadge status={lead.final_status} />
                  </td>
                  <td className="px-3 py-3 whitespace-nowrap">{formatDate(lead.submitted_at)}</td>
                  <td className="px-3 py-3 whitespace-nowrap">{formatDate(lead.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {pages > 1 ? (
        <div className="mt-4 flex items-center justify-between">
          <p className="text-sm text-sea-800/70">
            Page {page} of {pages}
          </p>
          <div className="flex gap-2">
            <Button variant="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </Button>
            <Button variant="secondary" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>
              Next
            </Button>
          </div>
        </div>
      ) : null}

      <Modal
        open={!!selected}
        title={selected ? `Lead #${selected.lead_number}` : 'Lead'}
        onClose={() => setSelected(null)}
        wide
      >
        {selected ? (
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Customer Number">
                <Input
                  readOnly={!isAdmin}
                  value={edit.customer_number}
                  onChange={(e) => setEdit((x) => ({ ...x, customer_number: e.target.value }))}
                />
              </Field>
              <Field label="DID">
                <Input
                  readOnly={!isAdmin}
                  value={edit.did}
                  onChange={(e) => setEdit((x) => ({ ...x, did: e.target.value }))}
                />
              </Field>
              <Field label="First Name">
                <Input
                  readOnly={!isAdmin}
                  value={edit.first_name}
                  onChange={(e) => setEdit((x) => ({ ...x, first_name: e.target.value }))}
                />
              </Field>
              <Field label="Last Name">
                <Input
                  readOnly={!isAdmin}
                  value={edit.last_name}
                  onChange={(e) => setEdit((x) => ({ ...x, last_name: e.target.value }))}
                />
              </Field>
              <Field label="State">
                <Select
                  disabled={!isAdmin}
                  value={edit.state}
                  onChange={(e) => setEdit((x) => ({ ...x, state: e.target.value }))}
                >
                  {(settings?.us_states || []).map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="ZipCode">
                <Input
                  readOnly={!isAdmin}
                  value={edit.zip_code}
                  onChange={(e) => setEdit((x) => ({ ...x, zip_code: e.target.value }))}
                />
              </Field>
              <Field label="Agent">
                <Select
                  disabled={!isAdmin}
                  value={edit.agent_id}
                  onChange={(e) => setEdit((x) => ({ ...x, agent_id: e.target.value }))}
                >
                  {agents.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Closer">
                <Select
                  disabled={!isAdmin}
                  value={edit.closer_id}
                  onChange={(e) => setEdit((x) => ({ ...x, closer_id: e.target.value }))}
                >
                  {closers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Campaign">
                <Select
                  disabled={!isAdmin}
                  value={edit.campaign_id}
                  onChange={(e) => setEdit((x) => ({ ...x, campaign_id: e.target.value }))}
                >
                  {campaigns.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="D1">
                <Input
                  readOnly={!isAdmin}
                  value={edit.d1}
                  onChange={(e) => setEdit((x) => ({ ...x, d1: e.target.value }))}
                />
              </Field>
              <Field label="Other">
                <Input
                  readOnly={!isAdmin}
                  value={edit.other}
                  onChange={(e) => setEdit((x) => ({ ...x, other: e.target.value }))}
                />
              </Field>
              <div className="sm:col-span-2">
                <Field label="Comments">
                  <TextArea
                    readOnly={!isAdmin}
                    rows={3}
                    value={edit.comments}
                    onChange={(e) => setEdit((x) => ({ ...x, comments: e.target.value }))}
                  />
                </Field>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Initial Status">
                <Input readOnly value={selected.initial_status} className="bg-sea-50" />
              </Field>
              <Field label="Buyer Response">
                <Select
                  disabled={!isAdmin}
                  value={edit.buyer_response}
                  onChange={(e) => setEdit((x) => ({ ...x, buyer_response: e.target.value }))}
                >
                  {(settings?.buyer_responses || []).map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Final Status">
                <Select
                  disabled={!isAdmin}
                  value={edit.final_status}
                  onChange={(e) => {
                    const next = e.target.value
                    setEdit((x) => ({
                      ...x,
                      final_status: next,
                      rejection_reason: next === 'Rejected' ? x.rejection_reason : '',
                    }))
                    setModalError('')
                  }}
                >
                  {(settings?.final_statuses || []).map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </Select>
              </Field>
              {edit.final_status === 'Rejected' ? (
                <Field label="Rejection Reason *" error={modalError && !edit.rejection_reason ? modalError : undefined}>
                  <Select
                    disabled={!isAdmin}
                    required
                    value={edit.rejection_reason}
                    onChange={(e) => {
                      setEdit((x) => ({ ...x, rejection_reason: e.target.value }))
                      setModalError('')
                    }}
                  >
                    <option value="">Select reason</option>
                    {(settings?.rejection_reasons || []).map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </Select>
                </Field>
              ) : null}
              <div className="sm:col-span-2">
                <Field label="Admin Notes">
                  <TextArea
                    readOnly={!isAdmin}
                    rows={3}
                    value={edit.admin_notes}
                    onChange={(e) => setEdit((x) => ({ ...x, admin_notes: e.target.value }))}
                  />
                </Field>
              </div>
            </div>

            <div className="grid gap-2 text-sm text-sea-800/80 sm:grid-cols-2">
              <p>Submitted At: {formatDate(selected.submitted_at)}</p>
              <p>Buyer Response At: {formatDate(selected.buyer_response_at)}</p>
              <p>Finalized At: {formatDate(selected.finalized_at)}</p>
              <p>Updated At: {formatDate(selected.updated_at)}</p>
            </div>

            {isAdmin ? (
              <div className="space-y-3">
                {modalError ? (
                  <p className="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{modalError}</p>
                ) : null}
                <div className="flex flex-wrap gap-2">
                  <Button onClick={() => void saveLead()} disabled={saving}>
                    {saving ? 'Saving…' : 'Save Changes'}
                  </Button>
                  <Button variant="danger" onClick={() => void removeLead()}>
                    Delete Lead
                  </Button>
                </div>
              </div>
            ) : (
              <p className="rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-900">
                This record is locked. Only Admin can edit submitted leads.
              </p>
            )}
          </div>
        ) : null}
      </Modal>
    </div>
  )
}
