import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Button, Field, Input } from '../components/ui'

export default function LoginPage() {
  const { user, loading, login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!loading && user) return <Navigate to="/" replace />

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center px-4">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_#cfe8e2_0%,_transparent_55%),linear-gradient(135deg,#0b3a4a_0%,#176578_45%,#efe6d4_100%)]" />
      <div className="relative w-full max-w-md overflow-hidden rounded-3xl border border-white/30 bg-white/90 shadow-2xl backdrop-blur">
        <div className="bg-sea-900 px-8 py-8 text-white">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-sea-100/60">Internal Platform</p>
          <h1 className="mt-2 font-display text-4xl">Seagulls Communications</h1>
          <p className="mt-2 text-sm text-sea-100/75">Inhouse Sales CRM — sign in to continue</p>
        </div>
        <form onSubmit={onSubmit} className="space-y-4 px-8 py-8">
          <Field label="Email">
            <Input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" />
          </Field>
          <Field label="Password">
            <Input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          </Field>
          {error ? <p className="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p> : null}
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? 'Signing in…' : 'Sign in'}
          </Button>
          <p className="text-center text-xs text-sea-800/60">
            TEST accounts: admin@seagullsdemo.com / agent@seagullsdemo.com / closer@seagullsdemo.com
          </p>
        </form>
      </div>
    </div>
  )
}
