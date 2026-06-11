from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
from datetime import datetime
import re


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("username")
    @classmethod
    def alphanumeric_only(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username must be alphanumeric (letters, numbers, underscores only)")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Budget ────────────────────────────────────────────────────────────────────

class CategoryBudgets(BaseModel):
    food_dining_delivery: Optional[float] = Field(None, ge=0, le=1_000_000)
    shopping_fashion: Optional[float] = Field(None, ge=0, le=1_000_000)
    electronics_tech: Optional[float] = Field(None, ge=0, le=1_000_000)
    entertainment_subs: Optional[float] = Field(None, ge=0, le=1_000_000)
    health_lifestyle: Optional[float] = Field(None, ge=0, le=1_000_000)
    others: Optional[float] = Field(None, ge=0, le=1_000_000)


class BudgetSetup(BaseModel):
    master_monthly: float = Field(..., gt=0, le=1_000_000)
    categories: Optional[CategoryBudgets] = None


class BudgetUpdate(BaseModel):
    master_monthly: Optional[float] = Field(None, gt=0, le=1_000_000)
    categories: Optional[CategoryBudgets] = None


# ── Wallet ────────────────────────────────────────────────────────────────────

class WalletStateResponse(BaseModel):
    state: str
    spend_pct: float
    spent_amount: Optional[float] = None
    budget_amount: Optional[float] = None
    category_pcts: dict
    last_updated: Optional[datetime] = None
    stale: bool = False


# ── Purchases ─────────────────────────────────────────────────────────────────

class PurchaseManual(BaseModel):
    item_name: str = Field(..., min_length=1, max_length=200)
    platform: str
    amount: float = Field(..., gt=0, le=1_000_000)
    category: str


class PurchaseResponse(BaseModel):
    status: str
    message: Optional[str] = None
    purchase: Optional[dict] = None


# ── Nudges ────────────────────────────────────────────────────────────────────

class NudgeFireRequest(BaseModel):
    trigger_type: str
    platform: Optional[str] = None
    context: Optional[dict] = None


class NudgeRespondRequest(BaseModel):
    nudge_id: str
    response: str

    @field_validator("response")
    @classmethod
    def valid_response(cls, v: str) -> str:
        if v not in ("paused", "overridden"):
            raise ValueError("response must be 'paused' or 'overridden'")
        return v


class NudgeResponse(BaseModel):
    nudge_id: str
    tier: str
    state: str
    title: str
    body: str
    tag: str
    context: dict


# ── Reports ───────────────────────────────────────────────────────────────────

class MonthlyReportResponse(BaseModel):
    month: str
    budget_summary: dict
    nudge_summary: dict
    streak_summary: dict
    insights: dict
    stale: bool = False
