import { useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { dashboardApi, getErrorMessage } from '../services/api'
import type { DashboardData } from '../types'
import { useAuth } from '../context/AuthContext'
import { Card, EmptyState, LoadingBlock, PageHeader, Select, StatCard } from '../components/ui'

const COLORS = ['#15803d', '#b91c1c', '#ca8a04']

export default function DashboardPage() {
  const { user } = useAuth()
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const now = new Date()
  const [month, setMonth] = useState<number | ''>('')
  const [year, setYear] = useState<number | ''>('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError('')
      try {
        const res = await dashboardApi.get(
          month === '' ? undefined : month,
          year === '' ? undefined : year,
        )
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

  const statusData = data
    ? [
        { name: 'Accepted', value: data.summary.accepted },
        { name: 'Rejected', value: data.summary.rejected },
        { name: 'Pending', value: data.summary.pending },
      ]
    : []

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle={
          user?.role === 'admin'
            ? 'Live performance across all leads, agents, closers, and campaigns.'
            : user?.role === 'agent'
              ? 'Your agent performance and associated leads.'
              : 'Your closer submissions and outcomes.'
        }
        actions={
          <div className="flex gap-2">
            <Select
              value={month}
              onChange={(e) => setMonth(e.target.value ? Number(e.target.value) : '')}
              className="w-36"
            >
              <option value="">All months</option>
              {Array.from({ length: 12 }, (_, i) => (
                <option key={i + 1} value={i + 1}>
                  {new Date(2000, i, 1).toLocaleString('default', { month: 'long' })}
                </option>
              ))}
            </Select>
            <Select
              value={year}
              onChange={(e) => setYear(e.target.value ? Number(e.target.value) : '')}
              className="w-28"
            >
              <option value="">All years</option>
              {[now.getFullYear(), now.getFullYear() - 1, now.getFullYear() - 2].map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </Select>
          </div>
        }
      />

      {error ? <p className="mb-4 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p> : null}
      {loading || !data ? (
        <LoadingBlock />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <StatCard label="Total Forms Submitted" value={data.summary.total_leads} />
            <StatCard label="Accepted Leads" value={data.summary.accepted} />
            <StatCard label="Rejected Leads" value={data.summary.rejected} />
            <StatCard label="Pending Leads" value={data.summary.pending} />
            <StatCard label="Acceptance Rate" value={`${data.summary.acceptance_rate}%`} />
            <StatCard label="Rejection Rate" value={`${data.summary.rejection_rate}%`} />
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <Card>
              <h2 className="mb-4 font-display text-2xl">Sales Status Distribution</h2>
              {data.summary.total_leads === 0 ? (
                <EmptyState title="No leads yet" description="Submit a sales form to populate the dashboard." />
              ) : (
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={statusData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90}>
                        {statusData.map((_, i) => (
                          <Cell key={i} fill={COLORS[i % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              )}
            </Card>

            <Card>
              <h2 className="mb-4 font-display text-2xl">Monthly Sales Trend</h2>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data.monthly_trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#d5e4e1" />
                    <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="accepted" stroke="#15803d" strokeWidth={2} />
                    <Line type="monotone" dataKey="rejected" stroke="#b91c1c" strokeWidth={2} />
                    <Line type="monotone" dataKey="pending" stroke="#ca8a04" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>

          {user?.role !== 'agent' ? (
            <Card className="mt-4">
              <h2 className="mb-4 font-display text-2xl">Accepted Sales by Agent</h2>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.agent_performance.slice(0, 8)}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#d5e4e1" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-15} textAnchor="end" height={60} />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="accepted" fill="#0f4d5f" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          ) : null}

          {user?.role !== 'closer' ? null : (
            <Card className="mt-4">
              <h2 className="mb-4 font-display text-2xl">Your Closer Outcomes</h2>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.closer_performance}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#d5e4e1" />
                    <XAxis dataKey="name" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="accepted" fill="#15803d" />
                    <Bar dataKey="rejected" fill="#b91c1c" />
                    <Bar dataKey="pending" fill="#ca8a04" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}

          {user?.role === 'admin' ? (
            <Card className="mt-4">
              <h2 className="mb-4 font-display text-2xl">Accepted Sales by Closer</h2>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.closer_performance.slice(0, 8)}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#d5e4e1" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-15} textAnchor="end" height={60} />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="accepted" fill="#176578" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          ) : null}

          <div className="mt-4 grid gap-4 lg:grid-cols-3">
            <Card>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-sea-700/70">Top Agent</p>
              <p className="mt-2 font-display text-2xl">{data.top_agent?.name || '—'}</p>
              <p className="text-sm text-sea-800/70">{data.top_agent ? `${data.top_agent.accepted} accepted` : 'No data'}</p>
            </Card>
            <Card>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-sea-700/70">Top Closer</p>
              <p className="mt-2 font-display text-2xl">{data.top_closer?.name || '—'}</p>
              <p className="text-sm text-sea-800/70">{data.top_closer ? `${data.top_closer.accepted} accepted` : 'No data'}</p>
            </Card>
            <Card>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-sea-700/70">Top Campaign</p>
              <p className="mt-2 font-display text-2xl">{data.top_campaign?.name || '—'}</p>
              <p className="text-sm text-sea-800/70">
                {data.top_campaign ? `${data.top_campaign.accepted} accepted` : 'No data'}
              </p>
            </Card>
          </div>
        </>
      )}
    </div>
  )
}
