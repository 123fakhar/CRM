import io
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from app.models import User
from app.services.leads import build_lead_query, lead_to_out


EXPORT_COLUMNS = [
    "Lead ID",
    "Customer Number",
    "First Name",
    "Last Name",
    "State",
    "ZipCode",
    "Agent",
    "Closer",
    "Campaign",
    "DID",
    "D1",
    "Other",
    "Comments",
    "Initial Status",
    "Buyer Response",
    "Final Status",
    "Rejection Reason",
    "Admin Notes",
    "Submitted At",
    "Buyer Response At",
    "Finalized At",
    "Updated At",
]


def _fmt(dt: datetime | None) -> str:
    if not dt:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def leads_dataframe(db: Session, user: User, **filters) -> pd.DataFrame:
    leads = build_lead_query(db, user, **filters).order_by(None).all()
    # re-order by submitted_at desc
    leads = sorted(leads, key=lambda l: l.submitted_at or datetime.min, reverse=True)
    rows = []
    for lead in leads:
        out = lead_to_out(lead)
        rows.append(
            {
                "Lead ID": out.lead_number,
                "Customer Number": out.customer_number,
                "First Name": out.first_name,
                "Last Name": out.last_name,
                "State": out.state,
                "ZipCode": out.zip_code,
                "Agent": out.agent_name,
                "Closer": out.closer_name,
                "Campaign": out.campaign_name,
                "DID": out.did,
                "D1": out.d1 or "",
                "Other": out.other or "",
                "Comments": out.comments or "",
                "Initial Status": out.initial_status,
                "Buyer Response": out.buyer_response,
                "Final Status": out.final_status,
                "Rejection Reason": out.rejection_reason or "",
                "Admin Notes": out.admin_notes or "",
                "Submitted At": _fmt(out.submitted_at),
                "Buyer Response At": _fmt(out.buyer_response_at),
                "Finalized At": _fmt(out.finalized_at),
                "Updated At": _fmt(out.updated_at),
            }
        )
    return pd.DataFrame(rows, columns=EXPORT_COLUMNS)


def export_csv(db: Session, user: User, **filters) -> bytes:
    df = leads_dataframe(db, user, **filters)
    return df.to_csv(index=False).encode("utf-8-sig")


def export_xlsx(db: Session, user: User, **filters) -> bytes:
    df = leads_dataframe(db, user, **filters)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads")
    return buffer.getvalue()
