import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  FileText,
  Users,
  UserCheck,
  Megaphone,
  BarChart3,
  ScrollText,
  Settings,
  LogOut,
  ClipboardPlus,
  Menu,
  X,
} from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'
import { useAuth } from '../context/AuthContext'
import type { Role } from '../types'

type NavItem = { to: string; label: string; icon: typeof LayoutDashboard; roles: Role[] }

const NAV: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, roles: ['admin', 'agent', 'closer'] },
  { to: '/leads', label: 'Leads', icon: FileText, roles: ['admin'] },
  { to: '/my-leads', label: 'My Leads', icon: FileText, roles: ['agent'] },
  { to: '/my-submissions', label: 'My Submissions', icon: FileText, roles: ['closer'] },
  { to: '/sales-form', label: 'Submit Sales Form', icon: ClipboardPlus, roles: ['admin', 'closer'] },
  { to: '/agents', label: 'Agents', icon: Users, roles: ['admin'] },
  { to: '/closers', label: 'Closers', icon: UserCheck, roles: ['admin'] },
  { to: '/campaigns', label: 'Campaigns', icon: Megaphone, roles: ['admin'] },
  { to: '/reports', label: 'Reports', icon: BarChart3, roles: ['admin', 'agent', 'closer'] },
  { to: '/users', label: 'Users', icon: Users, roles: ['admin'] },
  { to: '/audit', label: 'Audit Log', icon: ScrollText, roles: ['admin'] },
  { to: '/settings', label: 'Settings', icon: Settings, roles: ['admin'] },
]

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  if (!user) return null

  const items = NAV.filter((n) => n.roles.includes(user.role))

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[260px_1fr]">
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-30 w-[260px] border-r border-white/10 bg-sea-900 text-sea-100 transition lg:static lg:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex h-full flex-col">
          <div className="border-b border-white/10 px-5 py-6">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sea-100/60">Inhouse CRM</p>
            <h1 className="mt-1 font-display text-3xl text-white">Seagulls</h1>
            <p className="mt-1 text-sm text-sea-100/70">Communications</p>
          </div>
          <nav className="flex-1 space-y-1 overflow-y-auto p-3">
            {items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition',
                    isActive ? 'bg-white/15 text-white' : 'text-sea-100/75 hover:bg-white/10 hover:text-white',
                  )
                }
              >
                <item.icon size={18} />
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="border-t border-white/10 p-4">
            <p className="text-sm font-semibold text-white">{user.name}</p>
            <p className="text-xs capitalize text-sea-100/60">{user.role}</p>
            <button
              onClick={() => void handleLogout()}
              className="mt-3 inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-sea-100/80 hover:bg-white/10 hover:text-white"
            >
              <LogOut size={16} /> Logout
            </button>
          </div>
        </div>
      </aside>

      {open ? (
        <button className="fixed inset-0 z-20 bg-black/40 lg:hidden" onClick={() => setOpen(false)} />
      ) : null}

      <div className="min-w-0">
        <header className="sticky top-0 z-10 flex items-center gap-3 border-b border-sea-900/10 bg-sea-50/80 px-4 py-3 backdrop-blur lg:hidden">
          <button onClick={() => setOpen(true)} className="rounded-lg p-2 hover:bg-sea-900/5">
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
          <span className="font-display text-xl">Seagulls CRM</span>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
