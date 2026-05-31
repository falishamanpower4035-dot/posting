"""Niches CRUD — the personality + provider config for a content stream.

All routes auto-scope by tenant via the JWT dependency. The tenant scoping
middleware in db.session enforces this at the query level too — even if a
route forgot the manual filter, queries would still return only the current
tenant's rows.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from sma.db.models.niche import Niche
from sma.db.models.topic import TopicSource
from sma.db.session import get_db_session
from sma.web.auth.dependencies import CurrentUser
from sma.web.schemas.common import Page, PageMeta
from sma.web.schemas.niche import NicheCreate, NicheRead, NicheUpdate

router = APIRouter(prefix="/api/niches", tags=["niches"])

# Google News RSS is free + unlimited. We build a search query from the niche
# so every new niche gets an autonomous news source with zero manual setup.
_GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"


def _build_news_query(niche: Niche) -> str:
    """Derive a Google News search query from the niche's pillars (or name)."""
    import urllib.parse

    pillars = [p.split("(")[0].strip() for p in (niche.content_pillars or []) if p.strip()]
    terms = pillars[:4] if pillars else [niche.name]
    # OR the pillars together so the feed is broad but on-topic.
    raw = " OR ".join(f'"{t}"' for t in terms)
    return urllib.parse.quote(raw)


def _seed_rss_source(session, niche: Niche) -> None:
    """Auto-create an enabled RSS topic source for a new niche (idempotent)."""
    existing = session.execute(
        select(TopicSource).where(
            TopicSource.niche_id == niche.id, TopicSource.kind == "rss"
        )
    ).scalar_one_or_none()
    if existing is not None:
        return
    feed_url = _GOOGLE_NEWS_RSS.format(query=_build_news_query(niche))
    session.add(
        TopicSource(
            tenant_id=niche.tenant_id,
            niche_id=niche.id,
            kind="rss",
            config_json={"feed_urls": [feed_url], "items_per_feed": 10},
            enabled=True,
        )
    )


@router.get("", response_model=Page[NicheRead])
def list_niches(
    user: CurrentUser,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Page[NicheRead]:
    with get_db_session() as session:
        total = session.scalar(select(func.count(Niche.id))) or 0
        rows = session.scalars(
            select(Niche).order_by(Niche.id.desc()).limit(limit).offset(offset)
        ).all()
        return Page[NicheRead](
            items=[NicheRead.model_validate(r) for r in rows],
            meta=PageMeta(total=total, limit=limit, offset=offset),
        )


@router.post("", response_model=NicheRead, status_code=status.HTTP_201_CREATED)
def create_niche(payload: NicheCreate, user: CurrentUser) -> NicheRead:
    with get_db_session() as session:
        niche = Niche(tenant_id=user.tenant_id, **payload.model_dump())
        session.add(niche)
        session.flush()
        # Auto-seed a free Google News RSS source so the niche is autonomous
        # immediately — no manual Topic Source setup needed.
        _seed_rss_source(session, niche)
        session.flush()
        session.refresh(niche)
        return NicheRead.model_validate(niche)


@router.get("/{niche_id}", response_model=NicheRead)
def get_niche(niche_id: int, user: CurrentUser) -> NicheRead:
    with get_db_session() as session:
        niche = session.get(Niche, niche_id)
        if niche is None or niche.tenant_id != user.tenant_id:
            # Don't leak existence across tenants — same 404 for both cases.
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="niche not found")
        return NicheRead.model_validate(niche)


@router.patch("/{niche_id}", response_model=NicheRead)
def update_niche(niche_id: int, payload: NicheUpdate, user: CurrentUser) -> NicheRead:
    with get_db_session() as session:
        niche = session.get(Niche, niche_id)
        if niche is None or niche.tenant_id != user.tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="niche not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(niche, field, value)
        session.flush()
        session.refresh(niche)
        return NicheRead.model_validate(niche)


@router.delete("/{niche_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_niche(niche_id: int, user: CurrentUser) -> None:
    with get_db_session() as session:
        niche = session.get(Niche, niche_id)
        if niche is None or niche.tenant_id != user.tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="niche not found")
        session.delete(niche)
