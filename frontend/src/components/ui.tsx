import clsx from 'clsx'
import type { ReactNode } from 'react'

export function StatusBadge({ status }: { status: string }) {
  const tone =
    status === 'Accepted'
      ? 'bg-emerald-100 text-emerald-800 ring-emerald-200'
      : status === 'Rejected'
        ? 'bg-rose-100 text-rose-800 ring-rose-200'
        : status.includes('Pending')
          ? 'bg-amber-100 text-amber-900 ring-amber-200'
          : 'bg-slate-100 text-slate-700 ring-slate-200'
  return (
    <span className={clsx('inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold ring-1 ring-inset', tone)}>
      {status}
    </span>
  )
}

export function StatCard({
  label,
  value,
  hint,
}: {
  label: string
  value: string | number
  hint?: string
}) {
  return (
    <div className="rounded-2xl border border-sea-900/10 bg-white/80 p-5 shadow-sm backdrop-blur">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-sea-700/70">{label}</p>
      <p className="mt-2 font-display text-4xl text-sea-950">{value}</p>
      {hint ? <p className="mt-1 text-sm text-sea-800/70">{hint}</p> : null}
    </div>
  )
}

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string
  subtitle?: string
  actions?: ReactNode
}) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="font-display text-4xl text-sea-950">{title}</h1>
        {subtitle ? <p className="mt-1 text-sea-800/75">{subtitle}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  )
}

export function Button({
  children,
  variant = 'primary',
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
}) {
  const styles = {
    primary: 'bg-sea-900 text-white hover:bg-sea-800',
    secondary: 'bg-white text-sea-900 ring-1 ring-sea-900/15 hover:bg-sea-50',
    danger: 'bg-rose-700 text-white hover:bg-rose-800',
    ghost: 'bg-transparent text-sea-800 hover:bg-sea-900/5',
  }
  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50',
        styles[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={clsx(
        'w-full rounded-xl border border-sea-900/15 bg-white px-3 py-2.5 text-sm outline-none ring-sea-600/30 focus:ring-2',
        props.className,
      )}
    />
  )
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={clsx(
        'w-full rounded-xl border border-sea-900/15 bg-white px-3 py-2.5 text-sm outline-none ring-sea-600/30 focus:ring-2',
        props.className,
      )}
    />
  )
}

export function TextArea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      className={clsx(
        'w-full rounded-xl border border-sea-900/15 bg-white px-3 py-2.5 text-sm outline-none ring-sea-600/30 focus:ring-2',
        props.className,
      )}
    />
  )
}

export function Label({ children }: { children: ReactNode }) {
  return <label className="mb-1.5 block text-sm font-medium text-sea-900">{children}</label>
}

export function Field({
  label,
  children,
  error,
}: {
  label: string
  children: ReactNode
  error?: string
}) {
  return (
    <div>
      <Label>{label}</Label>
      {children}
      {error ? <p className="mt-1 text-xs text-rose-700">{error}</p> : null}
    </div>
  )
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={clsx('rounded-2xl border border-sea-900/10 bg-white/85 p-5 shadow-sm backdrop-blur', className)}>
      {children}
    </div>
  )
}

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-sea-900/20 bg-white/50 px-6 py-12 text-center">
      <p className="font-display text-2xl text-sea-900">{title}</p>
      {description ? <p className="mt-2 text-sm text-sea-800/70">{description}</p> : null}
    </div>
  )
}

export function LoadingBlock({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center rounded-2xl border border-sea-900/10 bg-white/70 py-16 text-sea-800/70">
      {label}
    </div>
  )
}

export function Toast({
  message,
  tone = 'success',
  onClose,
}: {
  message: string
  tone?: 'success' | 'error'
  onClose: () => void
}) {
  return (
    <div
      className={clsx(
        'fixed right-4 top-4 z-50 max-w-sm rounded-xl px-4 py-3 text-sm font-medium shadow-lg',
        tone === 'success' ? 'bg-emerald-700 text-white' : 'bg-rose-700 text-white',
      )}
    >
      <div className="flex items-start gap-3">
        <span className="flex-1">{message}</span>
        <button onClick={onClose} className="opacity-80 hover:opacity-100">
          ×
        </button>
      </div>
    </div>
  )
}

export function Modal({
  open,
  title,
  children,
  onClose,
  wide,
}: {
  open: boolean
  title: string
  children: ReactNode
  onClose: () => void
  wide?: boolean
}) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-40 flex items-start justify-center overflow-y-auto bg-sea-950/40 p-4 backdrop-blur-sm">
      <div
        className={clsx(
          'my-8 w-full rounded-2xl border border-sea-900/10 bg-white shadow-xl',
          wide ? 'max-w-4xl' : 'max-w-2xl',
        )}
      >
        <div className="flex items-center justify-between border-b border-sea-900/10 px-5 py-4">
          <h2 className="font-display text-2xl text-sea-950">{title}</h2>
          <button onClick={onClose} className="rounded-lg px-2 py-1 text-sea-700 hover:bg-sea-50">
            Close
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  )
}

export function formatDate(value?: string | null) {
  if (!value) return '—'
  const d = new Date(value)
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}
