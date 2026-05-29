"""Shared OAuth helpers.

Used by Meta / YouTube / TikTok / LinkedIn routers. Each platform has its own
wire format but the high-level flow is identical:

    /api/oauth/<platform>/connect  → 302 redirect to platform's authorize URL
    /api/oauth/<platform>/callback → exchanges code → token, saves SocialAccount

This module owns state-token generation, PKCE, lookup, and the post-callback
SocialAccount upsert path that all platforms converge on.
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from loguru import logger
from sqlalchemy import select

from sma.db.crypto import encrypt_blob
from sma.db.models.oauth_state import OAuthState
from sma.db.models.social_account import SocialAccount
from sma.db.session import get_session_factory


def get_base_url() -> str:
    """Public base URL of the FastAPI service. OAuth callbacks live under this."""
    return os.environ.get("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")


def callback_url(platform: str) -> str:
    return f"{get_base_url()}/api/oauth/{platform}/callback"


# ─── State + PKCE ──────────────────────────────────────────────


def issue_state(tenant_id: int, platform: str, redirect_after: str | None = None,
                with_pkce: bool = False) -> tuple[str, str | None]:
    """Generate a random state token, persist it, return (state, code_verifier_or_None)."""
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64) if with_pkce else None

    SessionLocal = get_session_factory()
    with SessionLocal() as session:
        session.add(
            OAuthState(
                state=state,
                tenant_id=tenant_id,
                platform=platform,
                code_verifier=code_verifier,
                redirect_after=redirect_after,
                created_at=datetime.now(timezone.utc),
            )
        )
        session.commit()
    return state, code_verifier


def consume_state(state: str, expected_platform: str) -> OAuthState:
    """Look up + delete the state row; verify platform; raise 400 on any mismatch."""
    SessionLocal = get_session_factory()
    with SessionLocal() as session:
        row = session.execute(
            select(OAuthState).where(OAuthState.state == state)
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=400, detail="invalid or expired OAuth state")
        # Expire states older than 30 minutes.
        if datetime.now(timezone.utc) - row.created_at > timedelta(minutes=30):
            session.delete(row)
            session.commit()
            raise HTTPException(status_code=400, detail="OAuth state expired; please retry")
        if row.platform != expected_platform:
            raise HTTPException(status_code=400, detail="OAuth state platform mismatch")
        # Snapshot before delete so caller can use the values.
        captured = OAuthState(
            id=row.id,
            state=row.state,
            tenant_id=row.tenant_id,
            platform=row.platform,
            code_verifier=row.code_verifier,
            redirect_after=row.redirect_after,
            created_at=row.created_at,
        )
        session.delete(row)
        session.commit()
        return captured


def pkce_challenge(code_verifier: str) -> str:
    """S256 code challenge for OAuth PKCE."""
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


# ─── Save the SocialAccount after a successful exchange ────────


def upsert_social_account(
    tenant_id: int,
    platform: str,
    account_handle: str,
    token_payload: dict,
    refresh_expires_at: datetime | None,
) -> int:
    """Insert or update a SocialAccount for (tenant, platform, account_handle).

    Returns the row id. token_payload is encrypted with Fernet before storage.
    """
    SessionLocal = get_session_factory()
    with SessionLocal() as session:
        existing = session.execute(
            select(SocialAccount).where(
                SocialAccount.tenant_id == tenant_id,
                SocialAccount.platform == platform,
                SocialAccount.account_handle == account_handle,
            ).execution_options(skip_tenant_filter=True)
        ).scalar_one_or_none()
        encrypted = encrypt_blob(token_payload)
        if existing is None:
            row = SocialAccount(
                tenant_id=tenant_id,
                platform=platform,
                account_handle=account_handle,
                encrypted_oauth_blob=encrypted,
                refresh_token_expires_at=refresh_expires_at,
                status="active",
            )
            session.add(row)
            session.flush()
            row_id = row.id
        else:
            existing.encrypted_oauth_blob = encrypted
            existing.refresh_token_expires_at = refresh_expires_at
            existing.status = "active"
            row_id = existing.id
        session.commit()
        return row_id


def env_creds(prefix: str, *names: str) -> dict[str, str]:
    """Read OAuth client creds from env vars (e.g. META_APP_ID, META_APP_SECRET).

    Returns a dict { name.lower(): value }. Raises HTTPException(503) if any
    required var is missing (so the operator sees a clear setup error).
    """
    creds: dict[str, str] = {}
    missing: list[str] = []
    for name in names:
        full = f"{prefix}_{name}"
        val = os.environ.get(full, "").strip()
        if not val:
            missing.append(full)
        creds[name.lower()] = val
    if missing:
        raise HTTPException(
            status_code=503,
            detail=(
                f"{prefix} OAuth not configured — missing env vars: {missing}. "
                f"Set them in .env and restart."
            ),
        )
    return creds
