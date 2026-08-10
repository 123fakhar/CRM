import { useEffect, useState } from 'react'
import { dashboardApi, downloadExport, getErrorMessage } from '../services/api'
import type { DashboardData, LeadFilters } from '../types'
import { useAuth } from '../context/AuthContext'
import {
  Button,
  Card,
  EmptyState,
  LoadingBlock,
  PageHeader,
  Select,
  StatCard,
  Toast,
} from '../components/ui'

function PerformanceTable({
  title,
  rows,
  submittedLabel = 'Total Leads',
}: {
  title: string
  rows: DashboardData['agent_performance']
  submittedLabel?: string
}) {
  return (
    <Card className="overflow-x-auto p-0">
      <div className="border-b border-sea-900/10 px-5 py-4">
        <h2 className="font-display text-2xl">{title}</h2>
      </div>
      {rows.length === 0 ? (
        <div className="p-5">
          <EmptyState title="No data" />
        </div>
      ) : (
        <table className="min-w-full text-left text-sm">
          <thead className="bg-sea-50">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3 text-right">{submittedLabel}</th>
              <th className="px-4 py-3 text-right">Accepted</th>
              <th className="px-4 py-3 text-right">Rejected</th>
              <th className="px-4 py-3 text-right">Pending</th>
              <th className="px-4 py-3 text-right">Acceptance Rate</th>
              <th className="px-4 py-3 text-right">Rejection Rate</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-t border-sea-900/10">
                <td className="px-4 py-3 font-medium">{row.name}</td>
                <td className="px-4 py-3 text-right">{row.total_leads}</td>
                <td className="px-4 py-3 text-right">{row.accepted}</td>
                <td className="px-4 py-3 text-right">{row.rejected}</td>
                <td className="px-4 py-3 text-right">{row.pending}</td>
                <td className="px-4 py-3 text-right">{row.acceptance_rate}%</td>
                <td className="px-4 py-3 text-right">{row.rejection_rate}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  )
}

export default function ReportsPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const now = new Date()
  const [month, setMonth] = useState<number>(now.getMonth() + 1)
  const [year, setYear] = useState<number>(now.getFullYear())
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      try {
        const res = await dashboardApi.get(month, year)
        if (!cancelled) setData(res)
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
  }, [month, year])

  async function exportFile(format: 'csv' | 'xlsx') {
    try {
      const filters: LeadFilters = { month, year }
      await downloadExport(format, filters)
      setToast(`${format.toUpperCase()} export downloaded.`)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div>
      <PageHeader
        title="Reports"
        subtitle={`Monthly reporting for ${new Date(year, month - 1, 1).toLocaleString('default', { month: 'long', year: 'numeric' })}`}
        actions={
          <div className="flex flex-wrap gap-2">
            <Select className="w-40" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
              {Array.from({ length: 12 }, (_, i) => (
                <option key={i + 1} value={i + 1}>
                  {new Date(2000, i, 1).toLocaleString('default', { month: 'long' })}
                </option>
              ))}
            </Select>
            <Select className="w-28" value={year} onChange={(e) => setYear(Number(e.target.value))}>
              {[now.getFullYear(), now.getFullYear() - 1, now.getFullYear() - 2].map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </Select>
            {isAdmin ? (
              <>
                <Button variant="secondary" onClick={() => void exportFile('csv')}>
                  Export CSV
                </Button>
                <Button variant="secondary" onClick={() => void exportFile('xlsx')}>
                  Export Excel
                </Button>
              </>
            ) : null}
          </div>
        }
      />

      {toast ? <Toast message={toast} onClose={() => setToast('')} /> : null}
      {error ? <p className="mb-4 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p> : null}

      {loading || !data ? (
        <LoadingBlock />
      ) : (
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <StatCard label="Total Leads" value={data.summary.total_leads} />
            <StatCard label="Accepted Sales" value={data.summary.accepted} />
            <StatCard label="Rejected Leads" value={data.summary.rejected} />
            <StatCard label="Pending Leads" value={data.summary.pending} />
            <StatCard label="Acceptance Rate" value={`${data.summary.acceptance_rate}%`} />
            <StatCard label="Rejection Rate" value={`${data.summary.rejection_rate}%`} />
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            <Card>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-sea-700/70">
                Most Accepted — Agent
              </p>
              <p className="mt-2 font-display text-2xl">{data.top_agent?.name || '—'}</p>
              <p className="text-sm text-sea-800/70">{data.top_agent?.accepted ?? 0} accepted sales</p>
            </Card>
            <Card>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-sea-700/70">
                Most Accepted — Closer
              </p>
              <p className="mt-2 font-display text-2xl">{data.top_closer?.name || '—'}</p>
              <p className="text-sm text-sea-800/70">{data.top_closer?.accepted ?? 0} accepted sales</p>
            </Card>
            <Card>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-sea-700/70">
                Most Accepted — Campaign
              </p>
              <p className="mt-2 font-display text-2xl">{data.top_campaign?.name || '—'}</p>
              <p className="text-sm text-sea-800/70">{data.top_campaign?.accepted ?? 0} accepted sales</p>
            </Card>
          </div>

          <PerformanceTable title="Agent Performance" rows={data.agent_performance} />
          <PerformanceTable
            title="Closer Performance"
            rows={data.closer_performance}
            submittedLabel="Forms Submitted"
          />
          <PerformanceTable title="Campaign Performance" rows={data.campaign_performance} />
        </div>
      )}
    </div>
  )
}
