import axios from 'axios'
import type {
  Agent,
  AppSettings,
  AuditEntry,
  Campaign,
  Closer,
  DashboardData,
  Lead,
  LeadFilters,
  PaginatedLeads,
  User,
} from '../types'

const api = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

function cleanParams(params?: Record<string, unknown>) {
  if (!params) return undefined
  const out: Record<string, unknown> = {}
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') out[k] = v
  })
  return out
}

export const authApi = {
  login: async (email: string, password: string) => {
    const { data } = await api.post<{ access_token: string }>('/auth/login/json', { email, password })
    return data
  },
  me: async () => {
    const { data } = await api.get<User>('/auth/me')
    return data
  },
  logout: async () => {
    await api.post('/auth/logout')
  },
}

export const leadsApi = {
  list: async (filters: LeadFilters = {}) => {
    const { data } = await api.get<PaginatedLeads>('/leads', { params: cleanParams(filters as Record<string, unknown>) })
    return data
  },
  get: async (id: number) => {
    const { data } = await api.get<Lead>(`/leads/${id}`)
    return data
  },
  create: async (payload: Record<string, unknown>) => {
    const { data } = await api.post<Lead>('/leads', payload)
    return data
  },
  update: async (id: number, payload: Record<string, unknown>) => {
    const { data } = await api.patch<Lead>(`/leads/${id}`, payload)
    return data
  },
  remove: async (id: number) => {
    const { data } = await api.delete<{ message: string }>(`/leads/${id}`)
    return data
  },
}

export const dashboardApi = {
  get: async (month?: number, year?: number) => {
    const { data } = await api.get<DashboardData>('/dashboard', {
      params: cleanParams({ month, year }),
    })
    return data
  },
}

export const agentsApi = {
  list: async (activeOnly = false) => {
    const { data } = await api.get<Agent[]>('/agents', { params: { active_only: activeOnly } })
    return data
  },
  create: async (payload: { name: string; active?: boolean }) => {
    const { data } = await api.post<Agent>('/agents', payload)
    return data
  },
  update: async (id: number, payload: Partial<Agent>) => {
    const { data } = await api.patch<Agent>(`/agents/${id}`, payload)
    return data
  },
  remove: async (id: number) => {
    const { data } = await api.delete<{ message: string }>(`/agents/${id}`)
    return data
  },
}

export const closersApi = {
  list: async (activeOnly = false) => {
    const { data } = await api.get<Closer[]>('/closers', { params: { active_only: activeOnly } })
    return data
  },
  create: async (payload: { name: string; active?: boolean }) => {
    const { data } = await api.post<Closer>('/closers', payload)
    return data
  },
  update: async (id: number, payload: Partial<Closer>) => {
    const { data } = await api.patch<Closer>(`/closers/${id}`, payload)
    return data
  },
  remove: async (id: number) => {
    const { data } = await api.delete<{ message: string }>(`/closers/${id}`)
    return data
  },
}

export const campaignsApi = {
  list: async (activeOnly = false) => {
    const { data } = await api.get<Campaign[]>('/campaigns', { params: { active_only: activeOnly } })
    return data
  },
  create: async (payload: { name: string; active?: boolean }) => {
    const { data } = await api.post<Campaign>('/campaigns', payload)
    return data
  },
  update: async (id: number, payload: Partial<Campaign>) => {
    const { data } = await api.patch<Campaign>(`/campaigns/${id}`, payload)
    return data
  },
  remove: async (id: number) => {
    const { data } = await api.delete<{ message: string }>(`/campaigns/${id}`)
    return data
  },
}

export const usersApi = {
  list: async () => {
    const { data } = await api.get<User[]>('/users')
    return data
  },
  create: async (payload: Record<string, unknown>) => {
    const { data } = await api.post<User>('/users', payload)
    return data
  },
  update: async (id: number, payload: Record<string, unknown>) => {
    const { data } = await api.patch<User>(`/users/${id}`, payload)
    return data
  },
  resetPassword: async (id: number, new_password: string) => {
    const { data } = await api.post<{ message: string }>(`/users/${id}/reset-password`, { new_password })
    return data
  },
  remove: async (id: number) => {
    const { data } = await api.delete<{ message: string }>(`/users/${id}`)
    return data
  },
}

export const auditApi = {
  list: async (params: { page?: number; page_size?: number; search?: string; entity?: string } = {}) => {
    const { data } = await api.get<{
      items: AuditEntry[]
      total: number
      page: number
      page_size: number
      pages: number
    }>('/audit', { params: cleanParams(params) })
    return data
  },
}

export const settingsApi = {
  get: async () => {
    const { data } = await api.get<AppSettings>('/settings')
    return data
  },
}

export async function downloadExport(format: 'csv' | 'xlsx', filters: LeadFilters = {}) {
  const token = localStorage.getItem('token')
  const params = new URLSearchParams()
  params.set('format', format)
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') params.set(k, String(v))
  })
  const res = await fetch(`/api/reports/export?${params.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error('Export failed')
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = format === 'xlsx' ? 'seagulls_leads_export.xlsx' : 'seagulls_leads_export.csv'
  a.click()
  URL.revokeObjectURL(url)
}

export function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail.map((d) => d.msg || JSON.stringify(d)).join(', ')
    }
  }
  if (err instanceof Error) return err.message
  return 'Something went wrong'
}

export default api
