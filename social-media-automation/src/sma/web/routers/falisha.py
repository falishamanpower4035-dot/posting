"""Falisha CRM integration endpoints.

Authentication: a shared API key passed as the `X-Falisha-Key` header.
Set FALISHA_POSTING_API_KEY on both this service and the Falisha frontend.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from sma.config import get_settings
from sma.falisha import service as falisha_service

router = APIRouter(prefix="/falisha", tags=["falisha"])


def _require_key(x_falisha_key: str = Header(default="")) -> None:
    cfg = get_settings()
    expected = cfg.falisha_posting_api_key
    if not expected:
        raise HTTPException(status_code=503, detail="FALISHA_POSTING_API_KEY not configured on server")
    if x_falisha_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")


class PostLeadRequest(BaseModel):
    lead_id: str


# ─── GET /falisha/config ──────────────────────────────────────────────────────
@router.get("/config")
def get_config(_: None = Depends(_require_key)) -> dict:
    return {"configured": falisha_service.is_configured()}


# ─── POST /falisha/post-lead ──────────────────────────────────────────────────
@router.post("/post-lead")
def post_lead(body: PostLeadRequest, _: None = Depends(_require_key)) -> dict:
    if not falisha_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Facebook or Supabase not fully configured — set META_PAGE_TOKEN, META_PAGE_ID, FALISHA_SUPABASE_URL, FALISHA_SUPABASE_SERVICE_KEY",
        )
    try:
        result = falisha_service.post_job_lead(body.lead_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
