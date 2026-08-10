from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int | None = None
    role: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    role: str
    active: bool = True


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    agent_name: str | None = None
    closer_name: str | None = None


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    role: str | None = None
    active: bool | None = None
    agent_name: str | None = None
    closer_name: str | None = None


class PasswordReset(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str
    active: bool
    created_at: datetime
    updated_at: datetime
    agent_id: int | None = None
    closer_id: int | None = None
    agent_name: str | None = None
    closer_name: str | None = None


class MeOut(UserOut):
    pass


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    active: bool = True
    user_id: int | None = None


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    active: bool | None = None


class AgentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    user_id: int | None
    active: bool
    created_at: datetime


class CloserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    active: bool = True
    user_id: int | None = None


class CloserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    active: bool | None = None


class CloserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    user_id: int | None
    active: bool
    created_at: datetime


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    active: bool = True


class CampaignUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    active: bool | None = None


class CampaignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    active: bool
    created_at: datetime


class LeadCreate(BaseModel):
    customer_number: str = Field(min_length=1, max_length=64)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=2, max_length=2)
    zip_code: str = Field(min_length=5, max_length=10)
    agent_id: int
    campaign_id: int
    did: str = Field(min_length=1, max_length=64)
    d1: str | None = Field(default=None, max_length=255)
    other: str | None = Field(default=None, max_length=255)
    comments: str | None = None


class LeadAdminUpdate(BaseModel):
    customer_number: str | None = Field(default=None, min_length=1, max_length=64)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=2)
    zip_code: str | None = Field(default=None, min_length=5, max_length=10)
    agent_id: int | None = None
    closer_id: int | None = None
    campaign_id: int | None = None
    did: str | None = Field(default=None, min_length=1, max_length=64)
    d1: str | None = Field(default=None, max_length=255)
    other: str | None = Field(default=None, max_length=255)
    comments: str | None = None
    buyer_response: str | None = None
    final_status: str | None = None
    rejection_reason: str | None = None
    admin_notes: str | None = None


class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_number: int
    customer_number: str
    first_name: str
    last_name: str
    state: str
    zip_code: str
    agent_id: int
    closer_id: int
    campaign_id: int
    agent_name: str
    closer_name: str
    campaign_name: str
    did: str
    d1: str | None
    other: str | None
    comments: str | None
    initial_status: str
    buyer_response: str
    final_status: str
    rejection_reason: str | None
    admin_notes: str | None
    submitted_at: datetime
    buyer_response_at: datetime | None
    finalized_at: datetime | None
    updated_at: datetime
    created_by: int
    updated_by: int | None


class PaginatedLeads(BaseModel):
    items: list[LeadOut]
    total: int
    page: int
    page_size: int
    pages: int


class StatsSummary(BaseModel):
    total_leads: int
    accepted: int
    rejected: int
    pending: int
    acceptance_rate: float
    rejection_rate: float


class PerformanceRow(BaseModel):
    id: int
    name: str
    total_leads: int
    accepted: int
    rejected: int
    pending: int
    acceptance_rate: float
    rejection_rate: float


class MonthlyTrendPoint(BaseModel):
    month: str
    accepted: int
    rejected: int
    pending: int
    total: int


class DashboardOut(BaseModel):
    summary: StatsSummary
    agent_performance: list[PerformanceRow]
    closer_performance: list[PerformanceRow]
    campaign_performance: list[PerformanceRow]
    monthly_trend: list[MonthlyTrendPoint]
    top_agent: PerformanceRow | None = None
    top_closer: PerformanceRow | None = None
    top_campaign: PerformanceRow | None = None


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    user_name: str
    role: str
    action: str
    entity: str
    entity_id: str | None
    old_value: str | None
    new_value: str | None
    timestamp: datetime


class PaginatedAudit(BaseModel):
    items: list[AuditLogOut]
    total: int
    page: int
    page_size: int
    pages: int


class MessageOut(BaseModel):
    message: str
    data: dict[str, Any] | None = None


class SettingsOut(BaseModel):
    app_name: str
    buyer_responses: list[str]
    final_statuses: list[str]
    rejection_reasons: list[str]
    us_states: list[str]
