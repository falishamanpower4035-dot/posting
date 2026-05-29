"""SocialAccount routes — read/list/delete.

OAuth flow handles creation; users connect via /api/oauth/{platform}/connect.
This router never returns the encrypted token blob.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from sma.db.models.social_account import SocialAccount
from sma.db.session import get_db_session
from sma.web.auth.dependencies import CurrentUser
from sma.web.schemas.common import Page, PageMeta
from sma.web.schemas.social_account import SocialAccountRead

router = APIRouter(prefix="/api/social-accounts", tags=["social-accounts"])


@router.get("", response_model=Page[SocialAccountRead])
def list_accounts(
    user: CurrentUser,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    platform: str | None = Query(None),
) -> Page[SocialAccountRead]:
    with get_db_session() as session:
        stmt = select(SocialAccount)
        if platform:
            stmt = stmt.where(SocialAccount.platform == platform)
        total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = session.scalars(
            stmt.order_by(SocialAccount.id.desc()).limit(limit).offset(offset)
        ).all()
        return Page[SocialAccountRead](
            items=[SocialAccountRead.model_validate(r) for r in rows],
            meta=PageMeta(total=total, limit=limit, offset=offset),
        )


@router.get("/{acct_id}", response_model=SocialAccountRead)
def get_account(acct_id: int, user: CurrentUser) -> SocialAccountRead:
    with get_db_session() as session:
        row = session.get(SocialAccount, acct_id)
        if row is None or row.tenant_id != user.tenant_id:
            raise HTTPException(status_code=404, detail="social account not found")
        return SocialAccountRead.model_validate(row)


@router.delete("/{acct_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(acct_id: int, user: CurrentUser) -> None:
    """Disconnect — deletes the stored OAuth tokens. User can re-connect via OAuth."""
    with get_db_session() as session:
        row = session.get(SocialAccount, acct_id)
        if row is None or row.tenant_id != user.tenant_id:
            raise HTTPException(status_code=404, detail="social account not found")
        session.delete(row)
