"""Current-user info — `/api/me`. Useful for the frontend to confirm a JWT works
and read user/tenant details for the navbar."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from sma.db.models.tenant import Tenant
from sma.db.models.user import User
from sma.db.session import get_db_session
from sma.web.auth.dependencies import CurrentUser
from sma.web.schemas.common import TimestampedRead

router = APIRouter(prefix="/api/me", tags=["me"])


class MeResponse(BaseModel):
    user_id: int
    tenant_id: int
    email: str
    role: str
    tenant_name: str
    subscription_status: str


@router.get("", response_model=MeResponse)
def me(user: CurrentUser) -> MeResponse:
    with get_db_session() as session:
        u = session.execute(
            select(User).where(User.id == user.user_id)
            .execution_options(skip_tenant_filter=True)
        ).scalar_one_or_none()
        t = session.execute(
            select(Tenant).where(Tenant.id == user.tenant_id)
            .execution_options(skip_tenant_filter=True)
        ).scalar_one_or_none()
        if u is None or t is None:
            raise HTTPException(status_code=404, detail="user not found")
        return MeResponse(
            user_id=u.id,
            tenant_id=t.id,
            email=u.email,
            role=u.role,
            tenant_name=t.name,
            subscription_status=t.subscription_status,
        )
