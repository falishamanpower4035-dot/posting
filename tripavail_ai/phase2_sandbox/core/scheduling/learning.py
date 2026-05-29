#!/usr/bin/env python3
from __future__ import annotations

from typing import List
from datetime import datetime
import pytz

# Try importing intelligence modules; fall back if unavailable
try:
    from core.content.intelligence.engagement_predictor import EngagementPredictor  # type: ignore
except Exception:
    EngagementPredictor = None  # type: ignore

try:
    from core.content.intelligence.seasonal_optimizer import SeasonalOptimizer  # type: ignore
except Exception:
    SeasonalOptimizer = None  # type: ignore

try:
    from core.content.intelligence.trending_detector import TrendingDetector  # type: ignore
except Exception:
    TrendingDetector = None  # type: ignore


PK_TZ = pytz.timezone("Asia/Karachi")
PEAK_WINDOW = list(range(19, 23))  # 7pm–11pm window (hours 19,20,21,22)
FALLBACK_PRIORITY = [18, 20, 21]    # Strong defaults if no learning available


class LearningScheduler:
    """Recommend peak posting hours (Pakistan time) based on learned patterns.

    Prefers 7–11pm local; orders hours by predicted engagement.
    """

    def __init__(self) -> None:
        self.now_pk = datetime.now(PK_TZ)

    def recommend_hours(self, k: int = 3) -> List[int]:
        scores: dict[int, float] = {}

        # Initialize with slight priors favoring 6pm/8pm/9pm
        for h in PEAK_WINDOW:
            scores[h] = 0.0
        for h, w in ((18, 0.2), (20, 0.3), (21, 0.25)):
            scores[h] = scores.get(h, 0.0) + w

        # Engagement predictor (historical platform performance)
        if EngagementPredictor is not None:
            try:
                pred = EngagementPredictor()
                for h in PEAK_WINDOW:
                    scores[h] += float(pred.predict_hourly_engagement(hour=h, tz="Asia/Karachi") or 0.0)
            except Exception:
                pass

        # Seasonal optimizer (weekday/season effects)
        if SeasonalOptimizer is not None:
            try:
                opt = SeasonalOptimizer()
                weekday = self.now_pk.weekday()
                for h in PEAK_WINDOW:
                    scores[h] += float(opt.score_hour(hour=h, weekday=weekday, tz="Asia/Karachi") or 0.0)
            except Exception:
                pass

        # Trending detector boost for near-term bursts
        if TrendingDetector is not None:
            try:
                trend = TrendingDetector()
                boost = trend.hourly_boosts(tz="Asia/Karachi")  # returns dict hour->boost
                for h, b in (boost or {}).items():
                    if h in PEAK_WINDOW:
                        scores[h] += float(b or 0.0)
            except Exception:
                pass

        # Sort hours by score, high to low; keep in-window only
        ranked = sorted([h for h in scores.keys()], key=lambda x: scores.get(x, 0.0), reverse=True)
        if not ranked:
            ranked = FALLBACK_PRIORITY.copy()
        # Return top-k unique hours
        out: List[int] = []
        for h in ranked:
            if h not in out:
                out.append(h)
            if len(out) >= k:
                break
        return out
