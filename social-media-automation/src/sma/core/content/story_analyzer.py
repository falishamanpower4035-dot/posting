"""Story analyzer — turns a Topic into a video production plan.

Output: narrative script + story beats (one per image) + duration estimates.
The analyzer doesn't generate any media; it just designs the plan.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from sma.core.niche.config import NicheConfig, VideoLength
from sma.core.templates import render
from sma.core.topics.base import Topic
from sma.providers.llm.base import LLMProvider


@dataclass
class StoryBeat:
    order: int
    scene_description: str
    voiceover_segment: str
    duration_sec: float


@dataclass
class StoryPlan:
    narrative_script: str
    duration_sec: float
    image_count: int
    hook_text: str
    story_beats: list[StoryBeat]
    raw: dict[str, Any] = field(default_factory=dict)


class StoryAnalysisError(Exception):
    pass


def analyze_story(
    topic: Topic,
    niche: NicheConfig,
    llm: LLMProvider,
    video_length: VideoLength | None = None,
) -> StoryPlan:
    length = video_length or niche.video_length_default
    prompt = render("story_analysis.j2", niche=niche, topic=topic, video_length=length)

    resp = llm.complete(
        system="You design vertical-video production plans. Return only valid JSON.",
        user=prompt,
        model=niche.llm_model,
        temperature=0.7,
        json_mode=True,
    )

    try:
        data = json.loads(resp.text)
    except json.JSONDecodeError as e:
        raise StoryAnalysisError(f"LLM returned invalid JSON: {e}\n{resp.text[:500]}") from e

    try:
        beats = [
            StoryBeat(
                order=int(b["order"]),
                scene_description=str(b["scene_description"]),
                voiceover_segment=str(b["voiceover_segment"]),
                duration_sec=float(b.get("duration_sec", 3.0)),
            )
            for b in data["story_beats"]
        ]
    except (KeyError, TypeError, ValueError) as e:
        raise StoryAnalysisError(f"Story plan is missing required beat fields: {e}") from e

    plan = StoryPlan(
        narrative_script=data["narrative_script"],
        duration_sec=float(data.get("duration_sec", sum(b.duration_sec for b in beats))),
        image_count=int(data.get("image_count", len(beats))),
        hook_text=str(data.get("hook_text", "")),
        story_beats=beats,
        raw=data,
    )

    if plan.image_count != len(plan.story_beats):
        logger.warning(
            f"Story plan declared image_count={plan.image_count} but produced "
            f"{len(plan.story_beats)} beats; using actual count"
        )
        plan.image_count = len(plan.story_beats)

    logger.info(
        f"Story plan: {plan.image_count} beats, ~{plan.duration_sec:.1f}s, "
        f"hook: {plan.hook_text!r}"
    )
    return plan
