# Phase 1 — Generalize the Engine (Detailed Task Breakdown)

> **Goal**: Take the working engine from `tripavail_ai/`, strip everything tourism-specific, wrap every external API call in a provider abstraction, make every prompt niche-driven, and prove it end-to-end with a non-tourism smoke test.
>
> **Duration**: ~2 weeks
>
> **Outcome**: A CLI that reads `niche.yaml`, fetches/generates topics, runs the full pipeline (story → images → voice → music → video → thumbnail), and posts to a configured platform — for *any* niche, not just tourism. Per-call cost tracking working. No web UI yet.

---

## 0. Repo Setup (Day 1, ~2 hours)

### 0.1 Create the new repo

```
D:\posty\social-media-automation\
```

Initialize:
- `git init`
- `pyproject.toml` (Python 3.11, Poetry or uv for dependency management — recommend **uv** for speed)
- `.gitignore` (Python defaults + `.env`, `data/`, `media/`, `*.mp4`, `__pycache__/`)
- `.env.example` (all env vars documented, no real secrets)
- `README.md` — minimal, will expand in Phase 4
- Pre-commit hooks: `ruff`, `black`, `mypy` (strict on new code)

### 0.2 Directory skeleton

```
social-media-automation/
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
├── src/
│   └── sma/                          # Python package (sma = social-media-automation)
│       ├── __init__.py
│       ├── core/
│       │   ├── niche/
│       │   │   ├── __init__.py
│       │   │   ├── config.py          # NicheConfig dataclass
│       │   │   └── loader.py          # YAML loader for Phase 1
│       │   ├── topics/
│       │   │   ├── __init__.py
│       │   │   ├── base.py            # TopicSource protocol + Topic dataclass
│       │   │   └── sources/
│       │   │       ├── __init__.py
│       │   │       ├── ai_generated.py
│       │   │       ├── manual.py
│       │   │       ├── rss.py
│       │   │       └── news.py        # genericized NewsData/NewsCatcher source
│       │   ├── content/
│       │   │   ├── __init__.py
│       │   │   ├── story_analyzer.py  # salvaged + genericized
│       │   │   ├── caption_generator.py # salvaged + genericized
│       │   │   └── post_manager.py    # salvaged, JSON for now (DB in Phase 2)
│       │   ├── media/
│       │   │   ├── __init__.py
│       │   │   ├── images/            # salvaged image-gen logic, refactored
│       │   │   ├── audio/             # salvaged TTS + music
│       │   │   └── video/             # salvaged ffmpeg assembly
│       │   ├── pipeline/
│       │   │   ├── __init__.py
│       │   │   ├── orchestrator.py    # main pipeline runner
│       │   │   ├── context.py         # PipelineContext (tenant_id placeholder, niche, providers)
│       │   │   └── lock.py            # salvaged file-lock utility
│       │   └── scheduling/
│       │       ├── __init__.py
│       │       └── scheduler.py       # salvaged, genericized
│       ├── providers/
│       │   ├── __init__.py
│       │   ├── registry.py            # central PROVIDERS dict + get_provider()
│       │   ├── llm/
│       │   │   ├── __init__.py
│       │   │   ├── base.py            # LLMProvider protocol
│       │   │   ├── openai.py
│       │   │   ├── anthropic.py       # stub for v1.1
│       │   │   └── gemini.py          # stub for v1.1
│       │   ├── image/
│       │   │   ├── __init__.py
│       │   │   ├── base.py            # ImageProvider protocol
│       │   │   ├── pexels.py
│       │   │   ├── unsplash.py
│       │   │   ├── nano_banana.py     # gemini-2.5-flash-image
│       │   │   └── dalle.py
│       │   ├── voice/
│       │   │   ├── __init__.py
│       │   │   ├── base.py            # VoiceProvider protocol
│       │   │   ├── elevenlabs.py
│       │   │   └── openai_tts.py
│       │   ├── music/
│       │   │   ├── __init__.py
│       │   │   ├── base.py            # MusicProvider protocol
│       │   │   └── elevenlabs.py
│       │   └── social/
│       │       ├── __init__.py
│       │       ├── base.py            # SocialPoster protocol + PostResult
│       │       ├── instagram.py       # salvaged
│       │       ├── facebook.py        # salvaged
│       │       ├── youtube.py         # salvaged
│       │       └── tiktok.py          # NEW
│       ├── usage/
│       │   ├── __init__.py
│       │   ├── events.py              # UsageEvent dataclass + sink
│       │   ├── pricing.py             # provider_pricing table (hardcoded YAML for Phase 1)
│       │   └── recorder.py            # record_usage() helper
│       └── cli/
│           ├── __init__.py
│           └── main.py                # Typer CLI: `sma run-once <niche.yaml>` etc.
├── templates/
│   ├── story_analysis.j2
│   ├── caption.j2
│   ├── hashtags.j2
│   ├── thumbnail_prompt.j2
│   ├── image_scene.j2
│   └── topic_scoring.j2
├── examples/
│   ├── fitness_niche.yaml             # smoke-test config
│   ├── recipes_niche.yaml
│   └── crypto_niche.yaml
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── data/                              # local dev only, gitignored
    ├── posts/
    ├── usage/
    └── topics/
```

### 0.3 Dependencies (pyproject.toml)

```toml
[project]
dependencies = [
    "openai>=1.50",
    "anthropic>=0.40",          # stubs for v1.1
    "google-genai>=0.3",        # Gemini + Nano Banana
    "elevenlabs>=1.0",
    "httpx>=0.27",
    "pydantic>=2.7",
    "pydantic-settings>=2.4",
    "loguru>=0.7",
    "jinja2>=3.1",
    "typer>=0.12",
    "ffmpeg-python>=0.2",
    "pillow>=10",
    "python-dotenv>=1.0",
    "pyyaml>=6.0",
    "tenacity>=9.0",            # retries
    "moviepy>=1.0",             # if existing video code uses it
]

[project.optional-dependencies]
dev = ["ruff", "black", "mypy", "pytest", "pytest-asyncio", "pytest-cov"]
```

---

## 1. Provider Abstraction Layer (Days 2-4)

This is the keystone. Every later task depends on it.

### 1.1 LLM provider

**`src/sma/providers/llm/base.py`**:
```python
from typing import Protocol, runtime_checkable
from dataclasses import dataclass

@dataclass
class LLMResponse:
    text: str
    tokens_in: int
    tokens_out: int
    model: str

@runtime_checkable
class LLMProvider(Protocol):
    name: str  # "openai" | "anthropic" | "gemini"
    def complete(
        self,
        system: str,
        user: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> LLMResponse: ...
```

**`src/sma/providers/llm/openai.py`**:
- Wraps `openai.OpenAI(api_key=...)`
- Returns `LLMResponse` with usage tokens populated
- Records `UsageEvent` after every call (see §6)
- Supports JSON mode via `response_format={"type": "json_object"}`
- Retries with `tenacity` on rate-limit / 5xx

`anthropic.py` and `gemini.py`: stub class implementing the protocol but raising `NotImplementedError` with a "coming in v1.1" message. Frees us to expose model selection in the registry without the work.

### 1.2 Image provider

**`src/sma/providers/image/base.py`**:
```python
@dataclass
class ImageResult:
    paths: list[Path]
    cost_usd: float       # 0.0 for Pexels/Unsplash
    provider: str
    metadata: dict        # source URLs, prompts used, etc.

@runtime_checkable
class ImageProvider(Protocol):
    name: str
    is_free: bool         # True for stock libs, False for paid generation
    def generate(
        self,
        prompts: list[str],
        aspect_ratio: str,        # "9:16" | "1:1" | "16:9"
        count: int,
    ) -> ImageResult: ...
```

Implementations:
- **`pexels.py`** — extract from existing `core/media/images/generator/generate_images.py` Pexels code path
- **`unsplash.py`** — extract from existing Unsplash fallback
- **`nano_banana.py`** — NEW. Uses `google-genai` SDK with model `gemini-2.5-flash-image`
- **`dalle.py`** — extract DALL-E path from `hybrid_generator.py`

### 1.3 Voice provider

**`src/sma/providers/voice/base.py`**:
```python
class VoiceProvider(Protocol):
    name: str
    def synthesize(self, text: str, voice_id: str, output_path: Path) -> VoiceResult: ...
```

Implementations:
- **`elevenlabs.py`** — extract from `core/media/audio/manager/elevenlabs_tts.py` and `core/media/audio/voiceover_generator_long.py`
- **`openai_tts.py`** — NEW. Cheaper alternative using OpenAI's TTS-1.

### 1.4 Music provider

Just **`elevenlabs.py`** for now — extract from `core/media/audio/elevenlabs_music.py`. Protocol defined for future Suno/AudioCraft providers.

### 1.5 Social poster

**`src/sma/providers/social/base.py`**:
```python
@dataclass
class PostResult:
    success: bool
    external_post_id: str | None
    url: str | None
    error: str | None
    raw_response: dict

class SocialPoster(Protocol):
    platform: str  # "instagram" | "facebook" | "youtube" | "tiktok"
    def post_video(
        self,
        video_path: Path,
        caption: str,
        hashtags: list[str],
        thumbnail_path: Path | None = None,
        is_short: bool = True,
    ) -> PostResult: ...
```

Implementations:
- **`instagram.py`** — extract from `tripavail_ai/core/social/platforms/instagram_poster.py`. Replace Dropbox temp upload with a generic "host video at public URL" hook (Phase 1: serve from local CLI; Phase 4: from R2/Railway).
- **`facebook.py`** — extract from `facebook_poster.py`. Keep file-lock logic.
- **`youtube.py`** — extract from `youtube_uploader.py`. Keep retry logic + Shorts upload.
- **`tiktok.py`** — NEW. TikTok Content Posting API: `/v2/post/publish/video/init/` → upload → `/v2/post/publish/status/fetch/`. Use `httpx` directly (no good Python SDK exists).

### 1.6 Provider registry

**`src/sma/providers/registry.py`**:
```python
PROVIDERS = {
    "llm": {"openai": OpenAIProvider, "anthropic": AnthropicProvider, "gemini": GeminiProvider},
    "image": {"pexels": PexelsProvider, "unsplash": UnsplashProvider,
              "nano_banana": NanoBananaProvider, "dalle": DalleProvider},
    "voice": {"elevenlabs": ElevenLabsVoice, "openai_tts": OpenAITTSVoice},
    "music": {"elevenlabs": ElevenLabsMusic},
    "social": {"instagram": InstagramPoster, "facebook": FacebookPoster,
               "youtube": YouTubePoster, "tiktok": TikTokPoster},
}

def get_provider(kind: str, name: str, credentials: dict) -> Any:
    cls = PROVIDERS[kind][name]
    return cls(**credentials)

def list_providers(kind: str, free_only: bool = False) -> list[str]:
    """Used by the future admin panel dropdowns."""
    ...
```

---

## 2. NicheConfig (Day 4-5)

### 2.1 Schema

**`src/sma/core/niche/config.py`**:
```python
from pydantic import BaseModel, Field

class NicheConfig(BaseModel):
    name: str                          # "Real Estate Tips"
    description: str                   # full prompt context block
    target_audience: str               # "first-time home buyers in the US"
    tone: str                          # "professional, friendly"
    content_pillars: list[str]         # ["mortgage tips", "market trends", ...]
    forbidden_topics: list[str] = []
    cta: str = ""                      # "Visit example.com to learn more"
    hashtag_seeds: list[str] = []      # base hashtags mixed into every post
    language: str = "en"
    video_length_default: str = "short"  # "short" | "long"

    # Provider preferences
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    image_provider: str = "pexels"     # safe free default
    voice_provider: str = "elevenlabs"
    voice_id: str = "default"
    music_provider: str = "elevenlabs"
```

### 2.2 YAML loader

**`src/sma/core/niche/loader.py`** — loads `niche.yaml`, validates with Pydantic.

### 2.3 Example niches

**`examples/fitness_niche.yaml`**:
```yaml
name: "Daily Fitness Tips"
description: |
  Quick, science-backed fitness and nutrition advice for busy professionals.
  Focus on actionable habits, not extreme regimens.
target_audience: "Working adults 25-45 who want to stay fit with limited time"
tone: "energetic, practical, encouraging"
content_pillars:
  - "5-minute workouts"
  - "meal prep hacks"
  - "myth-busting common fitness advice"
  - "habit-stacking for consistency"
forbidden_topics:
  - "extreme diets"
  - "supplement promotion"
cta: "Save this for your next gym session 💪"
hashtag_seeds: ["fitness", "health", "wellness", "workout"]
llm_model: "gpt-4o-mini"
image_provider: "pexels"
```

Plus `recipes_niche.yaml` and `crypto_niche.yaml` for breadth testing.

---

## 3. Prompt Templates (Day 5-6)

### 3.1 Move all hardcoded prompts to Jinja2

Audit current files for hardcoded prompt strings:
- `tripavail_ai/core/news/editor.py` — tourism scoring prompts
- `tripavail_ai/core/content/story_analyzer.py` — story analysis prompts
- `tripavail_ai/core/content/generator/generate_caption.py` — caption + hashtag prompts
- `tripavail_ai/core/media/images/generator/generate_images.py` — image scene prompts
- `tripavail_ai/core/media/images/generator/gemini_thumbnail_generator.py` — thumbnail prompts

For each, extract the prompt to a `templates/*.j2` file. Replace tourism-specific words with `{{ niche.* }}` variables.

Example **`templates/topic_scoring.j2`**:
```jinja
You are scoring topics for the niche: "{{ niche.name }}".

Niche description: {{ niche.description }}
Target audience: {{ niche.target_audience }}
Content pillars: {{ niche.content_pillars | join(", ") }}
{% if niche.forbidden_topics %}
Forbidden topics: {{ niche.forbidden_topics | join(", ") }}
{% endif %}

Score the following topic from 1-10 on its fit for this niche.
Output JSON: {"score": <int>, "reason": "<short>", "suggested_angle": "<one sentence>"}

Topic title: {{ topic.title }}
Topic content: {{ topic.content }}
```

### 3.2 Template loader

**`src/sma/core/templates.py`**:
```python
from jinja2 import Environment, FileSystemLoader

_env = Environment(loader=FileSystemLoader("templates"), autoescape=False)

def render(template_name: str, **context) -> str:
    return _env.get_template(template_name).render(**context)
```

In Phase 2, this gets swapped for a DB-backed loader so users can edit templates in the admin panel.

---

## 4. Topic Sources (Day 6-7)

### 4.1 Base interface

**`src/sma/core/topics/base.py`**:
```python
@dataclass
class Topic:
    title: str
    content: str
    source: str            # which TopicSource produced it
    source_metadata: dict
    score: float | None = None  # populated after scoring

class TopicSource(Protocol):
    kind: str
    def discover(self, niche: NicheConfig, llm: LLMProvider) -> list[Topic]: ...
```

### 4.2 Implementations

- **`ai_generated.py`** (default for SaaS) — prompts the LLM with niche config: "Generate 10 fresh topic ideas for this niche". No external API needed.
- **`manual.py`** — reads from a static list in niche config or DB.
- **`rss.py`** — uses `feedparser`, pulls latest items from configured feeds, hands them to LLM for relevance scoring.
- **`news.py`** — generalized version of current `core/news/fetcher/fetch_news.py`. Takes niche keywords from config instead of hardcoded "travel|tourism|hotels".

### 4.3 Topic scoring

**`src/sma/core/topics/scorer.py`** — uses `templates/topic_scoring.j2` + LLM to score every discovered topic. Filters by threshold (default 7) defined per-niche.

---

## 5. Salvage + Generalize Existing Engine (Days 7-10)

The biggest chunk of work. Move file-by-file from `tripavail_ai/` into `src/sma/`, replacing hardcoded calls with provider abstractions and removing tourism-specific logic.

### 5.1 Story analyzer

`tripavail_ai/core/content/story_analyzer.py` → `src/sma/core/content/story_analyzer.py`

Changes:
- Replace direct `openai.ChatCompletion(...)` with `LLMProvider.complete(...)`
- Replace hardcoded prompt with `render("story_analysis.j2", niche=..., topic=...)`
- Drop tourism-specific fields like "destination_features", "best_visiting_time"
- Keep core output: `narrative_script`, `duration_sec`, `image_count`, `story_beats[]`

### 5.2 Caption generator

`tripavail_ai/core/content/generator/generate_caption.py` → `src/sma/core/content/caption_generator.py`

Same treatment. Inputs: `niche`, `topic`, `narrative_script`. Outputs: `caption`, `hashtags`.

### 5.3 Image generation

`tripavail_ai/core/media/images/generator/{generate_images,hybrid_generator,gemini_thumbnail_generator,thumbnail_generator}.py` → `src/sma/core/media/images/`

Refactor:
- The orchestration logic (loop over story beats, generate scene prompts, call provider, resize) stays.
- The actual API call lines move into provider implementations.
- Thumbnail generation uses Nano Banana by default in v1 (better than tourism's old Gemini code).

### 5.4 Audio (voiceover + music)

`tripavail_ai/core/media/audio/...` → `src/sma/core/media/audio/`

Salvage:
- `voiceover_generator_long.py` for chunked long-form TTS (still needed in long-video flow)
- `elevenlabs_music.py` music generation
- `manager/audio_ducking.py` mixing
- `manager/music_library.py` for stock music fallback if user has no ElevenLabs music API access

### 5.5 Video assembly

`tripavail_ai/core/media/video/generator/...` → `src/sma/core/media/video/`

This is the keep-as-is part — most complex code, least touched by the pivot.

Decision needed for Phase 1: which of these is the primary?
- `automated_video.py` — looks like the main orchestrator
- `pro_video.py` / `pro_video_simple.py` — variants
- `simple_video.py` / `python_video.py` — older?
- `final_video_assembler_long.py` + `day_video_assembler_long.py` — long-video path

**Action**: Read each, document what it does, pick **one** short-video path and **one** long-video path. Delete the rest. (Plan to do this on Day 7 and adjust §5 if the pick is non-obvious.)

### 5.6 Long video generalization

`tripavail_ai/core/content/generation/{itinerary,script}_generator_long.py` → `src/sma/core/content/long/`

These currently produce day-by-day travel itineraries. Generalize to "multi-section narrative" — works for:
- Travel itineraries (original use)
- Recipe step-by-steps
- Workout routines
- Crypto market recaps
- "Top 10 X" lists

Same template-driven approach: `templates/long/section_planner.j2`, `templates/long/section_script.j2`. The video assembly code (`day_video_assembler_long.py`) doesn't care about content semantics — it just stitches sections. Rename it to `section_video_assembler.py`.

### 5.7 Social posters

Move + refactor as described in §1.5. Each existing `*_poster.py` file becomes a clean implementation of the `SocialPoster` protocol.

### 5.8 Pipeline orchestrator

`tripavail_ai/core/pipeline/orchestrator/{guard,lock,state}.py` → `src/sma/core/pipeline/`

Salvage:
- `lock.py` (file lock for concurrent run prevention) — keep as-is
- `guard.py` (duplicate detection) — generalize from "news article ID" to "topic hash"
- `state.py` (post state machine) — keep, simplify

New: **`src/sma/core/pipeline/orchestrator.py`** — top-level entrypoint:
```python
def run_pipeline(
    niche: NicheConfig,
    topic: Topic,
    providers: ProviderBundle,
    output_dir: Path,
    video_length: str = "short",
) -> PipelineResult:
    # 1. Story analysis
    # 2. Image generation (parallel)
    # 3. Voiceover
    # 4. Music
    # 5. Video assembly (short or long path)
    # 6. Thumbnail
    # 7. Caption + hashtags
    # 8. Save metadata
```

### 5.9 Drop entirely

- `core/news/editor.py` (replaced by topic scorer)
- `core/news/fetcher/` (replaced by topic sources, news source generalized)
- `core/content/intelligence/seasonal_optimizer.py` (tourism-specific)
- `core/production/production_pipeline_long.py` (replaced by new orchestrator)
- All `scripts/*.py` (replaced by CLI in §7)

---

## 6. Usage Tracking (Day 11)

### 6.1 UsageEvent

**`src/sma/usage/events.py`**:
```python
@dataclass
class UsageEvent:
    timestamp: datetime
    tenant_id: int        # always 1 in Phase 1
    provider: str         # "openai" | "elevenlabs" | "nano_banana" | ...
    model: str            # "gpt-4o-mini" | "eleven_turbo_v2" | ...
    operation: str        # "complete" | "synthesize" | "generate" | ...
    tokens_in: int = 0
    tokens_out: int = 0
    units: int = 0        # for non-token providers (chars, seconds, images)
    cost_usd: float = 0.0
    post_id: str | None = None
    metadata: dict = field(default_factory=dict)
```

### 6.2 Pricing table

**`src/sma/usage/pricing.yaml`** (seeded with current rates, easy to update):
```yaml
openai:
  gpt-4o-mini:
    input_per_1m: 0.15
    output_per_1m: 0.60
  gpt-4o:
    input_per_1m: 2.50
    output_per_1m: 10.00
  tts-1:
    per_unit_cost: 0.000015   # per character
    unit_label: "char"
elevenlabs:
  eleven_turbo_v2:
    per_unit_cost: 0.00018    # per character (rough avg)
    unit_label: "char"
nano_banana:
  gemini-2.5-flash-image:
    per_unit_cost: 0.039      # per image
    unit_label: "image"
```

### 6.3 Recorder

**`src/sma/usage/recorder.py`**:
```python
def record(event: UsageEvent) -> None:
    """Phase 1: append to data/usage/events.jsonl. Phase 2: insert to DB."""
```

### 6.4 Wire into providers

Every provider implementation calls `usage.record(...)` in its return path. This is non-negotiable — no shortcuts. The cost dashboard depends on it being complete.

---

## 7. CLI (Day 12)

**`src/sma/cli/main.py`** using Typer:

```bash
sma run-once examples/fitness_niche.yaml
    # Discover topics → score → pick top → generate → save to data/posts/

sma run-once examples/fitness_niche.yaml --topic-id 42
    # Re-run for a specific previously-discovered topic

sma post examples/fitness_niche.yaml data/posts/post_001 --platform instagram
    # Post a previously-generated post

sma usage --month 2026-05
    # Print usage summary from events.jsonl

sma test-provider llm openai
    # Sends a tiny request, prints response or error
```

This CLI is the Phase 1 deliverable. It proves the engine works end-to-end without a backend or frontend.

---

## 8. Smoke Tests (Day 13)

### 8.1 End-to-end test for non-tourism niche

```bash
cp .env.example .env  # fill in BYOK keys
sma run-once examples/fitness_niche.yaml --max-topics 1
```

Expected output:
- `data/posts/post_001/metadata.json` (caption, hashtags, narrative)
- `data/posts/post_001/images/scene_*.jpg` (10 images)
- `data/posts/post_001/audio/voiceover.mp3`
- `data/posts/post_001/audio/music.mp3`
- `data/posts/post_001/video/final.mp4` (vertical 1080x1920, ~30s)
- `data/posts/post_001/thumbnail.jpg`
- `data/usage/events.jsonl` (rows for OpenAI + Pexels + ElevenLabs)

Manually verify:
- Video plays
- Voiceover talks about fitness, not tourism
- Caption mentions fitness audience
- Hashtags include `#fitness`
- Total cost in `events.jsonl` is reasonable (~$0.05-$0.15)

### 8.2 Repeat for `recipes_niche.yaml` and `crypto_niche.yaml`

If all three produce coherent on-niche content, **Phase 1 is done**.

### 8.3 Provider swap test

Run `fitness_niche.yaml` with `image_provider: nano_banana` instead of `pexels`. Verify Nano Banana is called and `usage/events.jsonl` records the cost.

### 8.4 Post test (optional, requires real account)

```bash
sma post examples/fitness_niche.yaml data/posts/post_001 --platform tiktok
```

Verify the video appears on TikTok. (This validates the new TikTok poster end-to-end.)

---

## 9. Documentation (Day 14)

Minimal — just what's needed to hand off to Phase 2:
- `docs/architecture.md` — diagram + module overview
- `docs/providers.md` — how to add a new provider (template implementation)
- `docs/niches.md` — how to write a `niche.yaml`
- `docs/usage-events.md` — schema + how cost is computed

---

## Order of Operations Summary

| Day | Task |
|---|---|
| 1 | Repo setup, dependency install, directory skeleton |
| 2-3 | Provider abstraction protocols + OpenAI LLM + ElevenLabs voice/music |
| 3-4 | Pexels, Unsplash, Nano Banana, DALL-E image providers |
| 4 | NicheConfig + YAML loader + example niches |
| 5-6 | Move prompts to Jinja2 templates |
| 6-7 | Topic sources + scorer |
| 7-8 | Salvage story analyzer, caption generator, image orchestration |
| 8-9 | Salvage audio + video assembly (pick the canonical short + long paths) |
| 9-10 | Salvage + refactor social posters; ADD TikTok |
| 10-11 | Pipeline orchestrator + Context object |
| 11 | Usage tracking layer wired into all providers |
| 12 | CLI |
| 13 | Smoke tests for 3 non-tourism niches |
| 14 | Docs + cleanup; ready for Phase 2 |

---

## Definition of Done for Phase 1

- [ ] Fresh repo at `D:\posty\social-media-automation\` with clean structure
- [ ] All 5 provider categories (LLM, image, voice, music, social) have working implementations
- [ ] Nano Banana provider verified end-to-end
- [ ] TikTok poster verified end-to-end (or documented as "auth pending" if app review delays)
- [ ] No tourism-specific code remains
- [ ] No hardcoded prompts — everything Jinja2-templated
- [ ] CLI runs the full pipeline for 3 distinct non-tourism niches
- [ ] Long-video flow works for at least one non-tourism niche (e.g. recipe)
- [ ] Usage events recorded for every provider call, costs computed
- [ ] All `tripavail_ai/`-related code is in the old directory; new repo is independent
