"""Falisha CRM integration endpoints.

The Falisha backend reads its own database and sends the job lead data here.
This service just formats it and posts to Facebook — no DB connection needed.

Authentication: X-Falisha-Key header (shared secret).
"""

from __future__ import annotations

from typing import Optional

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


class JobLeadPayload(BaseModel):
    title: str
    employer_name: Optional[str] = None
    city: Optional[str] = None
    country_name: Optional[str] = None
    country_code: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    position_category: Optional[str] = None
    description_snippet: Optional[str] = None
    source_url: Optional[str] = None


# ─── GET /falisha/config ──────────────────────────────────────────────────────
@router.get("/config")
def get_config(_: None = Depends(_require_key)) -> dict:
    return {"configured": falisha_service.is_configured()}


# ─── POST /falisha/post-lead ──────────────────────────────────────────────────
@router.post("/post-lead")
def post_lead(body: JobLeadPayload, _: None = Depends(_require_key)) -> dict:
    if not falisha_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Facebook not configured — set META_PAGE_TOKEN and META_PAGE_ID",
        )
    try:
        return falisha_service.post_job_lead(body.model_dump())
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
