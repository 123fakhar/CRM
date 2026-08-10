from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.security import AdminUser, AnyAuthUser
from app.core.database import get_db
from app.models import Campaign
from app.schemas import CampaignCreate, CampaignOut, CampaignUpdate, MessageOut
from app.services.audit import write_audit

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.get("", response_model=list[CampaignOut])
def list_campaigns(
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
    active_only: bool = False,
):
    q = db.query(Campaign)
    if active_only or current_user.role != "admin":
        q = q.filter(Campaign.active.is_(True))
    return q.order_by(Campaign.name.asc()).all()


@router.post("", response_model=CampaignOut, status_code=201)
def create_campaign(payload: CampaignCreate, admin: AdminUser, db: Session = Depends(get_db)):
    if db.query(Campaign).filter(Campaign.name == payload.name.strip()).first():
        raise HTTPException(status_code=409, detail="Campaign name already exists")
    campaign = Campaign(name=payload.name.strip(), active=payload.active)
    db.add(campaign)
    db.flush()
    write_audit(
        db,
        user=admin,
        action="Created Campaign",
        entity="Campaign",
        entity_id=campaign.id,
        new_value=campaign.name,
    )
    db.commit()
    db.refresh(campaign)
    return campaign


@router.patch("/{campaign_id}", response_model=CampaignOut)
def update_campaign(
    campaign_id: int, payload: CampaignUpdate, admin: AdminUser, db: Session = Depends(get_db)
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"]:
        clash = (
            db.query(Campaign)
            .filter(Campaign.name == data["name"].strip(), Campaign.id != campaign_id)
            .first()
        )
        if clash:
            raise HTTPException(status_code=409, detail="Campaign name already exists")
        data["name"] = data["name"].strip()
    for key, value in data.items():
        old = getattr(campaign, key)
        if old != value:
            write_audit(
                db,
                user=admin,
                action=f"Campaign {key.title()} Changed",
                entity="Campaign",
                entity_id=campaign.id,
                old_value=str(old),
                new_value=str(value),
            )
            setattr(campaign, key, value)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.delete("/{campaign_id}", response_model=MessageOut)
def delete_campaign(campaign_id: int, admin: AdminUser, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.leads:
        campaign.active = False
        write_audit(
            db,
            user=admin,
            action="Deactivated Campaign",
            entity="Campaign",
            entity_id=campaign.id,
            old_value="active",
            new_value="inactive",
        )
        db.commit()
        return MessageOut(message="Campaign has leads and was deactivated instead of deleted")
    write_audit(
        db,
        user=admin,
        action="Deleted Campaign",
        entity="Campaign",
        entity_id=campaign.id,
        old_value=campaign.name,
    )
    db.delete(campaign)
    db.commit()
    return MessageOut(message="Campaign deleted")
