"""LLM-driven topic scoring. Filters discovered topics by niche fit."""

from __future__ import annotations

import copy
import json
import os

from loguru import logger

from sma.core.niche.config import NicheConfig
from sma.core.templates import render
from sma.core.topics.base import Topic
from sma.providers.llm.base import LLMProvider

# Cost controls:
#   - Only score the first N candidates per cycle (a news/RSS pull can return
#     50+ articles; scoring every one is wasted LLM spend).
#   - Truncate each article's content before sending to the LLM so a single
#     long article can't blow up token cost.
#
# NOTE: keep this comfortably above the number a single feed pull returns, or
# the engine starves: a stable RSS feed surfaces the same top-N items every
# cycle, those get scored→used, and the fresh items further down the feed are
# never scored, so the SCORED pool runs dry. Scoring with gpt-4o-mini is ~$0.0001
# per topic, so 50 is still well under a cent per cycle. Override via env.
MAX_TOPICS_TO_SCORE = int(os.environ.get("MAX_TOPICS_TO_SCORE", "50"))
MAX_CONTENT_CHARS_FOR_SCORING = 600


def _truncate_for_scoring(topic: Topic) -> Topic:
    """Return a shallow copy of the topic with content clipped for cheap scoring."""
    if len(topic.content or "") <= MAX_CONTENT_CHARS_FOR_SCORING:
        return topic
    clipped = copy.copy(topic)
    clipped.content = topic.content[:MAX_CONTENT_CHARS_FOR_SCORING].rsplit(" ", 1)[0] + "…"
    return clipped


def score_topic(topic: Topic, niche: NicheConfig, llm: LLMProvider) -> Topic:
    """Score one topic in-place. Mutates and returns the same Topic for chaining."""
    prompt = render("topic_scoring.j2", niche=niche, topic=_truncate_for_scoring(topic))
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
    """Score topics (capped at MAX_TOPICS_TO_SCORE), sort highest first, return those above threshold."""
    cutoff = threshold if threshold is not None else niche.topic_score_threshold
    to_score = topics[:MAX_TOPICS_TO_SCORE]
    if len(topics) > MAX_TOPICS_TO_SCORE:
        logger.info(
            f"Scoring only the first {MAX_TOPICS_TO_SCORE} of {len(topics)} candidates "
            f"to control LLM cost"
        )
    scored = [score_topic(t, niche, llm) for t in to_score]
    kept = [t for t in scored if (t.score or 0) >= cutoff]
    kept.sort(key=lambda t: t.score or 0, reverse=True)
    logger.info(
        f"Scored {len(scored)} topics; kept {len(kept)} above threshold {cutoff} "
        f"for niche {niche.name!r}"
    )
    return kept
