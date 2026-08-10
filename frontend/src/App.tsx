import { Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import AppLayout from './components/AppLayout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import SalesFormPage from './pages/SalesFormPage'
import LeadsPage from './pages/LeadsPage'
import ReportsPage from './pages/ReportsPage'
import { AgentsPage, CampaignsPage, ClosersPage } from './pages/ManagePages'
import UsersPage from './pages/UsersPage'
import AuditPage from './pages/AuditPage'
import SettingsPage from './pages/SettingsPage'
import type { Role } from './types'
import { LoadingBlock } from './components/ui'

function Protected({ roles }: { roles?: Role[] }) {
  const { user, loading } = useAuth()
  if (loading) return <LoadingBlock label="Checking session…" />
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />
  return <Outlet />
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<Protected />}>
          <Route element={<AppLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route element={<Protected roles={['admin', 'closer']} />}>
              <Route path="sales-form" element={<SalesFormPage />} />
            </Route>
            <Route element={<Protected roles={['admin']} />}>
              <Route path="leads" element={<LeadsPage title="Lead Management" />} />
              <Route path="agents" element={<AgentsPage />} />
              <Route path="closers" element={<ClosersPage />} />
              <Route path="campaigns" element={<CampaignsPage />} />
              <Route path="users" element={<UsersPage />} />
              <Route path="audit" element={<AuditPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
            <Route element={<Protected roles={['agent']} />}>
              <Route path="my-leads" element={<LeadsPage title="My Leads" />} />
            </Route>
            <Route element={<Protected roles={['closer']} />}>
              <Route path="my-submissions" element={<LeadsPage title="My Submissions" />} />
            </Route>
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}
