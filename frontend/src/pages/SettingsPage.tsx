import { useEffect, useState } from 'react'
import { settingsApi } from '../services/api'
import type { AppSettings } from '../types'
import { Card, LoadingBlock, PageHeader } from '../components/ui'

export default function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings | null>(null)

  useEffect(() => {
    void settingsApi.get().then(setSettings)
  }, [])

  if (!settings) return <LoadingBlock />

  return (
    <div>
      <PageHeader
        title="Settings"
        subtitle="Application configuration and reference lists used across the CRM."
      />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="font-display text-2xl">Application</h2>
          <p className="mt-3 text-sm text-sea-800/80">
            <strong>Name:</strong> {settings.app_name}
          </p>
          <p className="mt-2 text-sm text-sea-800/80">
            Authentication uses JWT bearer tokens. Role checks are enforced on every API endpoint.
          </p>
          <p className="mt-2 text-sm text-sea-800/80">
            Primary database is <strong>PostgreSQL</strong>. Configure{" "}
            <code>DATABASE_URL</code> in <code>backend/.env</code>. SQLite is only used for
            automated tests.
          </p>
        </Card>
        <Card>
          <h2 className="font-display text-2xl">Final Statuses</h2>
          <ul className="mt-3 list-disc pl-5 text-sm text-sea-800/80">
            {settings.final_statuses.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </Card>
        <Card>
          <h2 className="font-display text-2xl">Buyer Responses</h2>
          <ul className="mt-3 list-disc pl-5 text-sm text-sea-800/80">
            {settings.buyer_responses.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </Card>
        <Card>
          <h2 className="font-display text-2xl">Rejection Reasons</h2>
          <ul className="mt-3 list-disc pl-5 text-sm text-sea-800/80">
            {settings.rejection_reasons.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </Card>
        <Card className="lg:col-span-2">
          <h2 className="font-display text-2xl">Google Form Integration</h2>
          <p className="mt-3 text-sm text-sea-800/80">
            The internal CRM Sales Form fully implements the Seagulls Communications Inhouse Sales Sheet
            field structure. External Google Forms API credentials were not available in this environment,
            so the Google Form itself was not created or linked.
          </p>
          <p className="mt-2 text-sm text-sea-800/80">
            To connect later, provide a Google Cloud service account with Forms API access, form ID, and
            optionally Apps Script / webhook mapping into <code>POST /api/leads</code>.
          </p>
        </Card>
      </div>
    </div>
  )
}
