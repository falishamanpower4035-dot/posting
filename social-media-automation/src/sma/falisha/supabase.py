"""Thin Supabase REST client for the Falisha database.

We talk directly to the PostgREST API instead of pulling in supabase-py to
keep this service's dependency footprint minimal.
"""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger


class FalishaSupabase:
    def __init__(self, url: str, service_key: str) -> None:
        if not url or not service_key:
            raise ValueError("FALISHA_SUPABASE_URL and FALISHA_SUPABASE_SERVICE_KEY must be set")
        self._rest = url.rstrip("/") + "/rest/v1"
        self._headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def get_job_lead(self, lead_id: str) -> dict[str, Any]:
        with httpx.Client(timeout=15.0) as client:
            r = client.get(
                f"{self._rest}/job_leads",
                headers=self._headers,
                params={
                    "id": f"eq.{lead_id}",
                    "select": "id,title,employer_name,city,country_name,country_code,salary_min,salary_max,salary_currency,position_category,description_snippet,source_url,fb_post_id",
                    "limit": "1",
                },
            )
            r.raise_for_status()
            rows = r.json()
            if not rows:
                raise ValueError(f"Job lead {lead_id!r} not found")
            return rows[0]

    def mark_lead_posted(self, lead_id: str, fb_post_id: str, fb_posted_at: str) -> None:
        with httpx.Client(timeout=15.0) as client:
            r = client.patch(
                f"{self._rest}/job_leads",
                headers=self._headers,
                params={"id": f"eq.{lead_id}"},
                json={"fb_post_id": fb_post_id, "fb_posted_at": fb_posted_at},
            )
            if r.status_code not in (200, 204):
                logger.error(f"Failed to mark lead {lead_id} posted: {r.status_code} {r.text}")
