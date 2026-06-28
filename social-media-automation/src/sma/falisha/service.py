"""Falisha job-lead → Facebook Page posting service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from loguru import logger

from sma.config import get_settings
from sma.falisha.supabase import FalishaSupabase
from sma.providers.social.facebook import FacebookPoster


COUNTRY_NAMES: dict[str, str] = {
    "ae": "UAE", "sa": "Saudi Arabia", "qa": "Qatar", "kw": "Kuwait",
    "om": "Oman", "bh": "Bahrain", "tr": "Turkey",
    "gb": "UK", "de": "Germany", "pl": "Poland",
}


def _fmt_salary(
    min_sal: float | None,
    max_sal: float | None,
    currency: str | None,
) -> str:
    if not min_sal and not max_sal:
        return ""
    cur = currency or ""
    if min_sal and max_sal and min_sal != max_sal:
        return f"{cur}{int(min_sal):,}–{int(max_sal):,}"
    return f"{cur}{int(min_sal or max_sal or 0):,}"


def _build_post_text(lead: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"🔍 Hiring Now: {lead['title']}")
    lines.append("")

    if lead.get("employer_name"):
        lines.append(f"🏢 {lead['employer_name']}")

    country_display = COUNTRY_NAMES.get(
        (lead.get("country_code") or "").lower(),
        lead.get("country_name") or "",
    )
    location = ", ".join(filter(None, [lead.get("city"), country_display]))
    if location:
        lines.append(f"📍 {location}")

    salary = _fmt_salary(lead.get("salary_min"), lead.get("salary_max"), lead.get("salary_currency"))
    if salary:
        lines.append(f"💰 {salary}")

    lines.append("")

    snippet = (lead.get("description_snippet") or "").strip()
    if snippet:
        lines.append(snippet[:280] + ("…" if len(snippet) > 280 else ""))
        lines.append("")

    tag = (lead.get("position_category") or "jobs").lower().replace(" ", "")
    lines.append(f"#hiring #recruitment #jobs #{tag}")

    return "\n".join(lines)


def is_configured() -> bool:
    cfg = get_settings()
    return bool(cfg.meta_page_token and cfg.meta_page_id and cfg.falisha_supabase_url and cfg.falisha_supabase_service_key)


def post_job_lead(lead_id: str) -> dict[str, Any]:
    """
    Fetch the job_lead from Falisha Supabase, post it to Facebook, record the result.
    Returns: {"post_id": str, "already_posted": bool}
    """
    cfg = get_settings()
    db = FalishaSupabase(cfg.falisha_supabase_url, cfg.falisha_supabase_service_key)
    fb = FacebookPoster(page_token=cfg.meta_page_token, page_id=cfg.meta_page_id)

    lead = db.get_job_lead(lead_id)
    if lead.get("fb_post_id"):
        logger.info(f"Lead {lead_id} already posted as {lead['fb_post_id']}")
        return {"post_id": lead["fb_post_id"], "already_posted": True}

    message = _build_post_text(lead)
    result = fb.post_text(message, link=lead.get("source_url") or None)

    if not result.success:
        raise RuntimeError(f"Facebook post failed: {result.error}")

    fb_posted_at = datetime.now(timezone.utc).isoformat()
    db.mark_lead_posted(lead_id, result.external_post_id or "", fb_posted_at)
    logger.info(f"Lead {lead_id} posted to Facebook as {result.external_post_id}")

    return {"post_id": result.external_post_id, "already_posted": False}
