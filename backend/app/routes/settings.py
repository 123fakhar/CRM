from fastapi import APIRouter

from app.auth.security import AnyAuthUser
from app.core.config import get_settings
from app.core.constants import US_STATES, BuyerResponse, FinalStatus, RejectionReason
from app.schemas import SettingsOut

router = APIRouter(prefix="/api/settings", tags=["settings"])
settings = get_settings()


@router.get("", response_model=SettingsOut)
def get_app_settings(current_user: AnyAuthUser):
    return SettingsOut(
        app_name=settings.app_name,
        buyer_responses=[b.value for b in BuyerResponse],
        final_statuses=[f.value for f in FinalStatus],
        rejection_reasons=[r.value for r in RejectionReason],
        us_states=US_STATES,
    )
