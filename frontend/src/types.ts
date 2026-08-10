export type Role = 'admin' | 'agent' | 'closer'

export interface User {
  id: number
  name: string
  email: string
  role: Role
  active: boolean
  created_at: string
  updated_at: string
  agent_id?: number | null
  closer_id?: number | null
  agent_name?: string | null
  closer_name?: string | null
}

export interface Agent {
  id: number
  name: string
  user_id: number | null
  active: boolean
  created_at: string
}

export interface Closer {
  id: number
  name: string
  user_id: number | null
  active: boolean
  created_at: string
}

export interface Campaign {
  id: number
  name: string
  active: boolean
  created_at: string
}

export interface Lead {
  id: number
  lead_number: number
  customer_number: string
  first_name: string
  last_name: string
  state: string
  zip_code: string
  agent_id: number
  closer_id: number
  campaign_id: number
  agent_name: string
  closer_name: string
  campaign_name: string
  did: string
  d1: string | null
  other: string | null
  comments: string | null
  initial_status: string
  buyer_response: string
  final_status: string
  rejection_reason: string | null
  admin_notes: string | null
  submitted_at: string
  buyer_response_at: string | null
  finalized_at: string | null
  updated_at: string
  created_by: number
  updated_by: number | null
}

export interface PaginatedLeads {
  items: Lead[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface StatsSummary {
  total_leads: number
  accepted: number
  rejected: number
  pending: number
  acceptance_rate: number
  rejection_rate: number
}

export interface PerformanceRow {
  id: number
  name: string
  total_leads: number
  accepted: number
  rejected: number
  pending: number
  acceptance_rate: number
  rejection_rate: number
}

export interface DashboardData {
  summary: StatsSummary
  agent_performance: PerformanceRow[]
  closer_performance: PerformanceRow[]
  campaign_performance: PerformanceRow[]
  monthly_trend: {
    month: string
    accepted: number
    rejected: number
    pending: number
    total: number
  }[]
  top_agent: PerformanceRow | null
  top_closer: PerformanceRow | null
  top_campaign: PerformanceRow | null
}

export interface AuditEntry {
  id: number
  user_id: number | null
  user_name: string
  role: string
  action: string
  entity: string
  entity_id: string | null
  old_value: string | null
  new_value: string | null
  timestamp: string
}

export interface AppSettings {
  app_name: string
  buyer_responses: string[]
  final_statuses: string[]
  rejection_reasons: string[]
  us_states: string[]
}

export interface LeadFilters {
  search?: string
  agent_id?: number
  closer_id?: number
  campaign_id?: number
  initial_status?: string
  buyer_response?: string
  final_status?: string
  state?: string
  date_preset?: string
  date_from?: string
  date_to?: string
  month?: number
  year?: number
  page?: number
  page_size?: number
}
