"""LLM-driven topic scoring. Filters discovered topics by niche fit."""

from __future__ import annotations

import json

from loguru import logger

from sma.core.niche.config import NicheConfig
from sma.core.templates import render
from sma.core.topics.base import Topic
from sma.providers.llm.base import LLMProvider


def score_topic(topic: Topic, niche: NicheConfig, llm: LLMProvider) -> Topic:
    """Score one topic in-place. Mutates and returns the same Topic for chaining."""
    prompt = render("topic_scoring.j2", niche=niche, topic=topic)
    try:
        resp = llm.complete(
            system="You score content topics for niche fit. Return only valid JSON.",
            user=prompt,
            model=niche.llm_model,
            temperature=0.3,
            json_mode=True,
        )
        data = json.loads(resp.text)
        topic.score = float(data.get("score", 0))
        topic.score_reason = data.get("reason", "")
        topic.suggested_angle = data.get("suggested_angle", "")
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.warning(f"Failed to score topic {topic.title!r}: {e}")
        topic.score = 0.0
    return topic


def score_and_filter(
    topics: list[Topic],
    niche: NicheConfig,
    llm: LLMProvider,
    threshold: float | None = None,
) -> list[Topic]:
    """Score all topics, sort highest first, return those above threshold."""
    cutoff = threshold if threshold is not None else niche.topic_score_threshold
    scored = [score_topic(t, niche, llm) for t in topics]
    kept = [t for t in scored if (t.score or 0) >= cutoff]
    kept.sort(key=lambda t: t.score or 0, reverse=True)
    logger.info(
        f"Scored {len(scored)} topics; kept {len(kept)} above threshold {cutoff} "
        f"for niche {niche.name!r}"
    )
    return kept
