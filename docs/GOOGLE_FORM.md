# Google Form Integration — Remaining Work

The CRM internal form **Seagulls Communications Inhouse Sales Sheet** is fully implemented with these fields:

- Customer Number
- First Name
- Last Name
- State
- ZipCode
- Agent Name (from Agents DB)
- Closer Name (from authenticated Closer)
- Campaign Name (from Campaigns DB)
- DID
- D1
- Other
- Comments

Buyer Response / Final Status / Rejection Reason are **not** on the Closer form (Admin-only).

## Why the Google Form was not created

No Google Forms API credentials / service account were available in this environment. Per project rules, the integration was not faked.

## What you need to connect later

1. Google Cloud project with **Google Forms API** enabled
2. Service account JSON key (or OAuth client) with access to create/manage forms
3. Optionally: Apps Script or Cloud Function webhook that maps form responses to:

```http
POST /api/leads
Authorization: Bearer <closer-or-service-token>
Content-Type: application/json
```

Payload shape matches `LeadCreate` in the backend schemas.

Suggested env vars (already noted in `.env.example`):

```env
GOOGLE_SERVICE_ACCOUNT_FILE=path/to/service-account.json
GOOGLE_FORM_ID=
```
