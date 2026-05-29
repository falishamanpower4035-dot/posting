# Social Media Automation — Commercial Product Architecture & Migration Plan

> Product name: **Social Media Automation** (working name). Fresh repo, clean slate. The current `tripavail_ai/` is abandoned — nothing in production to preserve. We salvage the working engine code (story analysis, video assembly, image/voice/music generators, platform posters) and build a generalized product around it.
>
> Two modes from one codebase:
>
> - **Mode A — License (single-tenant)**: First customer is **Tashfeen** (already paid). He deploys on his own Railway with his own domain. One admin user, BYOK, no billing.
> - **Mode B — SaaS (multi-tenant)**: Operator (you) deploys on your own Railway + domain. Users sign up, pay monthly subscription via Stripe, BYOK for OpenAI (they see their own spend in a cost dashboard), connect socials via your master OAuth apps. **7-day free trial → single paid tier (~$29-49/mo).**
>
> Both modes run identical engine code, switched by `DEPLOYMENT_MODE` env var.

---

## 1. Product Vision

### Two products, one codebase

**Mode A — License sale (Tashfeen first, others later)**
1. Customer pays one-time off-platform (Gumroad, LemonSqueezy, direct).
2. Receives Railway one-click deploy link + admin login credentials.
3. Single admin user runs setup wizard → niche prompts → BYOK keys → OAuth socials → schedule.
4. Bot runs on his domain, his accounts, his costs. You're hands-off after delivery.

**Mode B — SaaS subscription (your platform)**
1. Marketing → landing page → 7-day free trial signup.
2. After trial → ~$29-49/mo via Stripe.
3. Each subscriber gets an isolated tenant inside your one shared deploy.
4. Subscriber adds their own OpenAI key (BYOK), connects socials via **your** master OAuth apps (one-click "Connect Instagram" — you handle Meta App Review once).
5. Cost-tracking dashboard shows them: "this month you spent $X on OpenAI, $0 on images (free libraries used)".
6. Subscription pays you for the platform; OpenAI pays itself directly via the user's key.

### Why this model wins

- **One codebase, two revenue streams**: license sales fund development; SaaS funds growth.
- **No platform AI cost risk**: BYOK in both modes — you never carry OpenAI/ElevenLabs costs.
- **Free image libraries by default**: Pexels/Unsplash require only a free dev key, so users never face surprise image costs. Premium image providers (Nano Banana, DALL-E) are opt-in via their own keys.
- **Multi-tenancy designed in from day 1**: every domain table has `tenant_id` from Phase 2. In single-tenant mode there's just one tenant (id=1). No retrofitting later.
- **Master OAuth apps**: subscribers click "Connect Instagram" and it works. You go through Meta/Google/TikTok app review once, not per-user.

### Non-goals (explicitly out of scope for v1)

- Built-in analytics beyond what the platforms expose.
- Long-form YouTube content beyond the existing long-video flow (kept as a length toggle).
- Pass-through billing (we don't bill users for OpenAI on top of subscription — they pay OpenAI directly).
- Free SaaS tier (7-day trial only — filters for serious users, no abuse risk on free).

---

## 2. Architecture Overview

### Stack

| Layer | Choice | Rationale |
|---|---|---|
| **Backend** | FastAPI (Python 3.11+) | Keep existing Python pipeline; async + OpenAPI for free. |
| **Frontend** | Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui | Modern, deploys to Railway easily. |
| **Database** | PostgreSQL (Railway managed) | Replaces all JSON files. Multi-tenant from day 1 via `tenant_id`. |
| **ORM** | SQLAlchemy 2.0 + Alembic | Standard. Migrations matter for both modes. |
| **Job runner** | APScheduler in-process (Mode A) / Celery+Redis (Mode B at scale) | Single-tenant doesn't need a queue; SaaS adds Redis when concurrent tenant load grows. |
| **Object storage** | Local Railway volume (Mode A) / Cloudflare R2 (Mode B) | Mode A = simple/cheap. Mode B = unbounded media across tenants needs object storage. |
| **Auth** | JWT. Single admin in Mode A. Email+password signup in Mode B. | Mode flag toggles signup/login routes. |
| **Secrets** | Fernet encryption, master key from `MASTER_KEY` env var | Per-tenant encrypted blobs in Postgres. |
| **Billing** | Stripe Checkout + webhooks (Mode B only) | Disabled entirely in Mode A. |
| **Container** | Dockerfile (multi-stage) | Required for Railway template + portability. |
| **Deployment target** | Railway primary; Docker → Render / Fly.io / any host | Railway has the best one-click template UX. |

### The mode flag

```bash
DEPLOYMENT_MODE=single_tenant   # Tashfeen's deploy. No signup. No billing.
DEPLOYMENT_MODE=multi_tenant    # Your SaaS. Signup + Stripe enabled.
```

Mode A's Railway template ships with `DEPLOYMENT_MODE=single_tenant` baked in. Mode B's deploy (your own) sets it to `multi_tenant`. The same Docker image works for both.

### High-level diagram

```
                   ┌────────────────────────────────────┐
                   │   Customer's Railway Project       │
                   │                                    │
  Browser ──────▶  │  ┌──────────────────────────────┐  │
  (admin)          │  │   Next.js Admin Panel        │  │
                   │  │   (frontend service)         │  │
                   │  └────────────┬─────────────────┘  │
                   │               │ REST                │
                   │               ▼                     │
                   │  ┌──────────────────────────────┐  │
                   │  │   FastAPI Backend            │  │
                   │  │   - REST API for admin       │  │
                   │  │   - OAuth callback handlers  │  │
                   │  │   - Job orchestration        │  │
                   │  └────┬──────────┬──────────────┘  │
                   │       │          │                  │
                   │       ▼          ▼                  │
                   │  ┌─────────┐  ┌──────────────────┐ │
                   │  │ Worker  │  │  PostgreSQL      │ │
                   │  │ Process │  │  (Railway addon) │ │
                   │  │ APSched │  │                  │ │
                   │  └────┬────┘  └──────────────────┘ │
                   │       │                             │
                   │       ▼                             │
                   │  ┌──────────────────────────────┐  │
                   │  │   Pipeline Engine            │  │
                   │  │   (existing core/, refactored│  │
                   │  │    with provider abstraction)│  │
                   │  └────┬─────────────────────────┘  │
                   │       │                             │
                   │       ▼                             │
                   │  Local volume (or R2)               │
                   │  for generated media                │
                   └────────────────┬───────────────────┘
                                    │
                                    ▼
                          External APIs (BYOK):
                          OpenAI, Gemini, ElevenLabs,
                          Pexels, Meta, YouTube, TikTok
```

### Service topology on Railway

Three services in one Railway project:

1. **`web`** — FastAPI (uvicorn). Serves API + OAuth callbacks.
2. **`worker`** — APScheduler process running pipeline jobs.
3. **`frontend`** — Next.js admin panel (could also be served as static export from FastAPI to drop one service).
4. **`postgres`** — Railway-managed Postgres addon.
5. (Optional) **`redis`** — only if/when we move to Celery.

---

## 3. What We Keep vs. What We Change

### Keep (the moat — battle-tested)

| Module | What it does | Why we keep it |
|---|---|---|
| `core/content/story_analyzer.py` | Breaks topic into narrative beats | Core IP — works well, just needs prompt-injectable. |
| `core/content/generator/generate_caption.py` | Caption + hashtag gen | Same — make prompts configurable. |
| `core/media/images/generator/` | Image generation | Refactor to provider interface; existing logic becomes one provider. |
| `core/media/audio/elevenlabs_music.py` | Music gen | Keep as-is. |
| `core/media/audio/voiceover_generator_long.py` | TTS | Keep; expose voice ID as user setting. |
| `core/media/video/generator/` | FFmpeg video assembly | Keep entirely — this is *the* moat. |
| `core/social/platforms/{instagram,facebook,youtube}_poster.py` | Posting logic | Refactor to common `SocialPoster` interface; add TikTok. |
| Long-video flow (`*_long.py` files) | Long-form content | Keep — surfaced as a "video length" toggle in admin. |

### Change / replace

| Current | New |
|---|---|
| `core/news/fetcher/` (NewsData.io tourism queries) | **Generic content trigger system** — see §5.1. News is *one* kind of trigger; others = "topic list", "RSS feeds", "manual one-off", "AI-generated topic from niche prompt". |
| `core/news/editor.py` (hardcoded tourism scoring) | **Niche-aware scoring** — prompt template stored per-customer, scoring threshold configurable. |
| `data/scheduled_posts.json`, `data/raw_news.json`, etc. | **Postgres tables**: `topics`, `posts`, `media_assets`, `schedules`, `posting_attempts`. |
| `.env`-based single config | **`config` table** + per-provider `credentials` table (encrypted). |
| systemd timers + `scheduler_daemon.py` polling JSON | **APScheduler** triggered by DB schedules. |
| Hardcoded `core/social/platforms/instagram_poster.py` API call | **`SocialPoster` interface** with OAuth-based per-customer tokens. |
| `scripts/*.py` operational tooling | Replaced by admin panel UI buttons + REST endpoints. |

### Add (new)

- Next.js admin panel (entire frontend).
- FastAPI backend wrapping the engine.
- OAuth flows for Meta (IG+FB), YouTube, TikTok.
- TikTok Content Posting API client.
- Gemini Nano Banana (`gemini-2.5-flash-image`) as image provider.
- Provider abstraction layer (LLM, image, voice, music, social).
- Encrypted credentials store.
- License key validator (lightweight, optional — can skip in v1).
- Railway template + Dockerfile + deploy docs.

---

## 4. Provider Abstraction Layer (the most important refactor)

The single biggest architectural change. Today, `core/news/editor.py` calls `openai.ChatCompletion(...)` directly. Tomorrow, every external dependency goes through a provider interface so users can swap them.

### Interfaces (protocol classes in `core/providers/`)

```python
# core/providers/llm.py
class LLMProvider(Protocol):
    def complete(self, system: str, user: str, model: str, **kw) -> str: ...

# Implementations:
class OpenAIProvider(LLMProvider): ...
class AnthropicProvider(LLMProvider): ...   # optional v1.1
class GeminiProvider(LLMProvider): ...      # optional v1.1
```

```python
# core/providers/image.py
class ImageProvider(Protocol):
    def generate(self, prompt: str, aspect_ratio: str, count: int) -> list[Path]: ...

# Implementations:
class NanoBananaProvider(ImageProvider):  # gemini-2.5-flash-image
class DalleProvider(ImageProvider):       # OpenAI gpt-image-1 / dall-e-3
class PexelsProvider(ImageProvider):      # stock fallback
class UnsplashProvider(ImageProvider):    # stock fallback
```

```python
# core/providers/voice.py
class VoiceProvider(Protocol):
    def synthesize(self, text: str, voice_id: str) -> Path: ...

class ElevenLabsVoice(VoiceProvider): ...
class OpenAITTSVoice(VoiceProvider): ...   # cheaper alternative

# core/providers/music.py — same pattern
# core/providers/social.py:
class SocialPoster(Protocol):
    platform: str  # "instagram" | "facebook" | "youtube" | "tiktok"
    def post(self, video: Path, caption: str, hashtags: list[str], **kw) -> PostResult: ...
```

### Provider registry

```python
# core/providers/registry.py
PROVIDERS = {
    "llm": {"openai": OpenAIProvider, "anthropic": AnthropicProvider, "gemini": GeminiProvider},
    "image": {"nano_banana": NanoBananaProvider, "dalle": DalleProvider, "pexels": PexelsProvider, ...},
    "voice": {"elevenlabs": ElevenLabsVoice, "openai_tts": OpenAITTSVoice},
    "music": {"elevenlabs": ElevenLabsMusic, "suno": SunoMusic},
    "social": {"instagram": InstagramPoster, "facebook": FacebookPoster, "youtube": YouTubePoster, "tiktok": TikTokPoster},
}

def get_provider(kind: str, name: str, credentials: dict) -> Any:
    cls = PROVIDERS[kind][name]
    return cls(**credentials)
```

This is what makes "user picks model from dropdown" work without `if/elif` chains scattered through the codebase.

---

## 5. Generalizing the Trigger (replacing news fetcher)

### 5.1 Generic Topic Sources

Today the only way a post gets created is: news fetched → scored → if score ≥ 7 → generate. For a generalized product we need pluggable **topic sources**:

```python
# core/topics/sources.py
class TopicSource(Protocol):
    def discover(self, niche_config: NicheConfig) -> list[Topic]: ...

class NewsTopicSource(TopicSource):
    """Fetch from NewsData/NewsCatcher using niche keywords."""

class RSSTopicSource(TopicSource):
    """Pull from a list of RSS feeds the user provides."""

class ManualTopicSource(TopicSource):
    """User pastes a list of topics in the admin panel."""

class AIGeneratedTopicSource(TopicSource):
    """Ask the LLM 'give me 10 trending topics about <niche>'."""

class WebhookTopicSource(TopicSource):
    """User POSTs topics to /api/topics/webhook from their own systems."""
```

The customer picks one or more in the wizard. AI-generated is the default — works for anyone with no other inputs.

### 5.2 NicheConfig

```python
# core/niche/config.py
@dataclass
class NicheConfig:
    name: str                          # "Real Estate Tips"
    description: str                   # full prompt context
    target_audience: str               # "first-time home buyers in the US"
    tone: str                          # "professional, friendly"
    content_pillars: list[str]         # ["mortgage tips", "market trends", ...]
    forbidden_topics: list[str]        # ["specific addresses", "competitor names"]
    cta: str                           # "Visit example.com to learn more"
    hashtag_seeds: list[str]           # base hashtags to mix into every post
    language: str                      # "en"
```

This object is loaded from DB and threaded through every prompt. Replaces the hardcoded "tourism" assumptions.

### 5.3 Prompt template system

Every LLM call goes through a Jinja2 template stored in DB (with seeded defaults):

```
templates/
  story_analysis.j2
  caption.j2
  hashtags.j2
  thumbnail_prompt.j2
  image_scene.j2
  topic_scoring.j2
```

Power users can edit templates in the admin panel. Default templates ship with the product and reference `{{ niche.* }}`, `{{ topic.* }}` variables.

---

## 6. Data Model (Postgres)

**Every domain table carries `tenant_id`** so the same schema serves both modes. Mode A = one row in `tenants` (id=1), every query auto-scoped to it. Mode B = one row per subscriber.

```
tenants             (id, name, owner_user_id, subscription_status,
                     trial_ends_at, stripe_customer_id, stripe_subscription_id,
                     created_at)
                    -- subscription_status: trialing | active | past_due | cancelled | none
                    -- "none" used in Mode A (single-tenant, no billing)

users               (id, tenant_id, email, password_hash, role,
                     email_verified, created_at)
                    -- role: admin | member  (member reserved for future team feature)
                    -- Mode A: one admin user, tenant_id=1
                    -- Mode B: every signup creates a user + their own tenant

config              (tenant_id, key, value, encrypted)  -- per-tenant settings

niche               (id, tenant_id, name, description, audience, tone, pillars,
                     forbidden, cta, hashtag_seeds, language, updated_at)

credentials         (id, tenant_id, provider_kind, provider_name, label,
                     encrypted_blob, created_at)

social_accounts     (id, tenant_id, platform, account_name,
                     encrypted_oauth_blob, refresh_token_expires_at,
                     status, last_used_at)

prompt_templates    (id, tenant_id, slug, body, is_default, updated_at)

topic_sources       (id, tenant_id, kind, config_json, enabled, last_run_at)

topics              (id, tenant_id, source_id, raw_payload, normalized_title,
                     score, status, used_for_post_id, created_at)

posts               (id, tenant_id, topic_id, niche_id, status, video_length,
                     model_used, image_provider, voice_provider, music_provider,
                     caption, hashtags, narrative_script, story_beats_json,
                     created_at, generated_at, error_log)

media_assets        (id, tenant_id, post_id, kind, path_or_url, sha256,
                     generated_at)

schedules           (id, tenant_id, post_id, scheduled_for_utc,
                     platforms_json, status, attempts_count)

posting_attempts    (id, tenant_id, schedule_id, platform, attempted_at,
                     status, external_post_id, response_log, error)

posting_rules       (id, tenant_id, name, type, params_json, enabled)

-- NEW: cost transparency layer (used in BOTH modes; required for Mode B)
usage_events        (id, tenant_id, provider, model, operation,
                     tokens_in, tokens_out, units, cost_usd,
                     post_id, created_at)
                    -- One row per LLM/voice/music API call.
                    -- Powers the "you spent $X this month" dashboard.

provider_pricing    (provider, model, input_per_1m, output_per_1m,
                     per_unit_cost, unit_label, updated_at)
                    -- Static pricing table seeded with current OpenAI/ElevenLabs/etc rates.
                    -- Updated when providers change prices.
```

**SQLAlchemy automatic tenant scoping**: a session-level filter via `with_loader_criteria(...)` adds `WHERE tenant_id = :current_tenant` to every query. Single source of truth, impossible to forget. In Mode A the current tenant is always 1.

**Migration from current JSON files** is one-time on first boot: import script reads `data/scheduled_posts.json`, `data/posts/post_*/metadata.json`, etc., assigns them to `tenant_id=1`, and seeds the DB.

---

## 7. Admin Panel (Next.js)

### Page map (mode-aware)

Pages marked **A** appear only in single-tenant. Pages marked **B** appear only in multi-tenant. Unmarked pages exist in both.

| Route | Purpose | Mode |
|---|---|---|
| `/signup` | Email + password. Creates tenant + Stripe trial. | **B** |
| `/login` | Email/username + password. JWT issued. | both |
| `/billing` | Current plan, trial countdown, Stripe portal link, invoice history. | **B** |
| `/account` | Email, password change, delete account. | **B** |
| `/setup` | First-run wizard (niche → keys → socials → schedule). | both |
| `/dashboard` | Posts today, queued, last 5 attempts, system health. **+ this-month spend tile** in Mode B. | both |
| `/niche` | Edit `NicheConfig`. | both |
| `/prompts` | Prompt templates editor (Monaco). | both |
| `/keys` | BYOK credentials. Add/test/delete per provider. Test buttons verify keys. | both |
| `/socials` | OAuth into your master apps (one click per platform). | both |
| `/topics` | Discovered topics + scores. Manual reject/promote/add. | both |
| `/posts` | Table of all posts. Filters by status/platform/date. | both |
| `/posts/:id` | Video preview, edit, regenerate, post-now. | both |
| `/schedule` | Calendar view. Drag-to-reschedule. | both |
| `/sources` | Configure topic sources. | both |
| `/rules` | Peak/quiet hours, spacing, platform priority. | both |
| `/usage` | **Cost dashboard**: this month's OpenAI spend, ElevenLabs spend, breakdown by post/day, projected monthly. | both (more prominent in B) |
| `/logs` | Live log tail (SSE). | both |
| `/settings` | Master-key rotation, export/import config, admin user mgmt. | both |
| `/admin` | **Operator-only** (you, in Mode B): tenant list, MRR, churn, signups, ops actions. | **B**, role=operator |

### UX principles

- **Setup wizard is the make-or-break**: a non-technical buyer must be able to go from "fresh deploy" to "first post live" in under 30 minutes.
- **Test buttons everywhere**: every API key has a "Test" button that hits the provider with a tiny request and shows green/red.
- **Preview before commit**: every generated post must be previewable (video player, caption, hashtags) before going live. Default mode = "draft" (manual approval); power users can toggle to "auto-publish".
- **No jargon**: write copy for a marketer, not an engineer. "Bring your own OpenAI key" not "Configure LLM provider credentials".

---

## 8. OAuth & Social Posting

### Per-platform notes

| Platform | API | OAuth scopes needed | Gotchas |
|---|---|---|---|
| **Instagram** | Graph API `/media` + `/media_publish` | `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement` | Requires a connected Facebook Page + Instagram Business account. Existing code already handles this. Video must be hosted at a public URL (currently uses Dropbox; can move to R2). |
| **Facebook** | Graph API `/videos` | `pages_manage_posts`, `pages_read_engagement` | Page access token, not user. Existing code is solid. |
| **YouTube** | YouTube Data API v3 `videos.insert` | `https://www.googleapis.com/auth/youtube.upload` | Refresh tokens. Existing code handles Shorts. Quota = 10k units/day default; uploads cost 1600 units each → ~6 uploads/day per project. **Customer needs their own GCP project + OAuth client.** Document this. |
| **TikTok** | Content Posting API (`/v2/post/publish/video/init/`) | `video.publish`, `video.upload` | New for us. Requires TikTok for Developers app + audited app for unaudited mode limits. PHOTO posts have a separate endpoint. Video URL must be hosted publicly OR use FILE_UPLOAD with chunks. |

### Token storage

Each `social_accounts` row stores `{access_token, refresh_token, expires_at, scopes}` encrypted. A scheduled job refreshes tokens 24h before expiry.

### Why R2 (not Dropbox) for media hosting

Instagram and TikTok require publicly fetchable video URLs. Today the Instagram poster uploads to Dropbox temp storage. For a productized version:
- Default: serve media from the customer's own deploy via signed URLs (works for Railway public domain).
- Optional: customer plugs in Cloudflare R2 / S3 / Backblaze creds → signed URLs from there.

This avoids needing a Dropbox account as a hard prerequisite for buyers.

---

## 9. Migration Phases (Concrete Steps)

### **Phase 1 — Generalize the engine** (~2 weeks)

Goal: existing pipeline runs from a `NicheConfig` instead of hardcoded tourism, with provider abstraction.

1.1. Create `core/providers/` with protocol definitions (LLM, image, voice, music, social).
1.2. Refactor existing OpenAI calls to go through `LLMProvider`.
1.3. Refactor `core/media/images/generator/` to expose existing logic as `PexelsProvider` + `UnsplashProvider` (the "free" tier — these are SaaS defaults).
1.4. Add `NanoBananaProvider` (Gemini 2.5 Flash Image API) — paid, opt-in.
1.5. Add `OpenAITTSProvider` as cheaper voiceover alternative.
1.6. Refactor `core/social/platforms/*` to common `SocialPoster` interface.
1.7. Add `TikTokPoster`.
1.8. Create `core/niche/config.py` and thread `NicheConfig` through `story_analyzer`, `generate_caption`, prompts.
1.9. Move all prompt strings into `templates/*.j2` files (default templates, no DB yet).
1.10. Make video length a parameter (`short` ≤ 60s = current short flow; `long` ≥ 3min = current long-video flow). Single code path, length-conditional.
1.11. **Add `UsageEvent` recording at every provider call** (writes to a JSON file in Phase 1, swaps to DB in Phase 2). Foundation for cost dashboard.
1.12. Build smoke-test script: load a hardcoded `NicheConfig` for a non-tourism niche (e.g. "fitness tips"), run end-to-end, verify a video is produced and usage is logged.

**Deliverable**: CLI runs the pipeline for *any* niche given a YAML config. Tourism becomes one config among many. Per-call cost tracking working.

### **Phase 2 — Backend (FastAPI + Postgres) with multi-tenancy baked in** (~3 weeks)

2.1. Project layout: `apps/web/` (FastAPI) + `apps/worker/` (APScheduler) + shared `core/` library.
2.2. SQLAlchemy 2.0 models matching §6 schema, **with `tenant_id` on every domain table from day 1**.
2.3. **Tenant-scoping middleware**: `with_loader_criteria` automatically filters every query by current tenant. Single source of truth.
2.4. Alembic migrations.
2.5. Encrypted credentials store (Fernet, master key from `MASTER_KEY` env), per-tenant.
2.6. JWT auth. `DEPLOYMENT_MODE=single_tenant` → single admin user bootstrapped from env. `DEPLOYMENT_MODE=multi_tenant` → signup + login routes enabled.
2.7. REST endpoints (CRUD for niche, prompts, keys, socials, topics, posts, schedule, rules, usage; action endpoints for `regenerate`, `post-now`, `test-key`).
2.8. OAuth callback handlers for Meta, YouTube, TikTok — using **your master OAuth app credentials** (env vars: `META_CLIENT_ID`, `META_CLIENT_SECRET`, etc.). Mode A customers can override with their own apps if they want.
2.9. Worker process: APScheduler with three jobs — `discover_topics` (interval), `process_schedules` (every 60s), `refresh_oauth_tokens` (hourly).
2.10. **Usage events table populated by provider abstraction layer**, `provider_pricing` table seeded with current OpenAI/ElevenLabs/Gemini rates.
2.11. Pipeline trigger refactor: `core/pipeline/orchestrator/` reads from DB instead of JSON, **always within a tenant context**.
2.12. Migration script: import existing `data/posts/`, `data/scheduled_posts.json` into DB as `tenant_id=1`.
2.13. OpenAPI spec auto-generated for the frontend.

**Deliverable**: Backend works headless in both modes — Mode A serves a single tenant, Mode B accepts signups. Drivable via `curl`/Postman. Usage tracking populating the DB.

### **Phase 3 — Frontend (Next.js admin panel)** (~3-4 weeks)

3.1. Next.js 15 scaffold + Tailwind + shadcn/ui + TanStack Query + Zod.
3.2. Generate TS API client from OpenAPI spec (`openapi-typescript`).
3.3. Auth flow + protected routes. **Mode-aware route gating** — `/signup`, `/billing`, `/account` only render when `NEXT_PUBLIC_DEPLOYMENT_MODE=multi_tenant`.
3.4. Setup wizard (niche → keys → socials → schedule, with "Test" buttons throughout).
3.5. Dashboard page (with this-month spend tile in Mode B).
3.6. Niche editor.
3.7. Prompts editor (Monaco).
3.8. Keys page (test buttons calling `/api/credentials/:id/test`).
3.9. Socials page (OAuth start buttons → callback → token saved).
3.10. Topics + Sources pages.
3.11. Posts list + detail page (video preview, regenerate, edit, post-now).
3.12. Schedule calendar (use `react-big-calendar` or similar).
3.13. Rules editor.
3.14. **Usage / cost dashboard** — month-to-date spend by provider, breakdown per post, projected monthly. Powered by `usage_events` table.
3.15. Live logs page (SSE from backend).
3.16. Settings page.

**Deliverable**: Buyer can run the full product in a browser. End-to-end: deploy → wizard → first post live.

### **Phase 4 — Ship Mode A (Tashfeen)** (~1-2 weeks)

4.1. Multi-stage Dockerfile (frontend build → backend image with static assets baked in).
4.2. `railway.toml` + Railway template button (`https://railway.app/template/...`) with `DEPLOYMENT_MODE=single_tenant` defaulted.
4.3. Documentation:
    - 5-minute quickstart (deploy → first post)
    - Per-platform OAuth setup guides — for Mode A, customer either uses YOUR master apps (if you allow it) or creates their own. **Tashfeen will likely use his own** since he has his own brand.
    - Troubleshooting section
    - Video walkthrough recorded
4.4. License key check at startup (offline-signed JWT: you sign licenses with a private key, product validates with embedded public key). Lightweight, no phone-home.
4.5. Hand off Tashfeen's deploy: deploy template, hand him admin credentials, walk through wizard.

**Deliverable**: Tashfeen's deploy live and posting. First license customer onboarded.

### **Phase 5 — Ship Mode B (Your SaaS)** (~3-4 weeks)

Adds the SaaS-only layer. The engine and admin panel already work multi-tenant from Phase 2-3 — this phase is signup/billing/marketing.

5.1. **Stripe integration**:
   - Stripe Checkout session for signup → 7-day trial → auto-charge.
   - Webhook handler for `customer.subscription.{created,updated,deleted}`, `invoice.payment_{succeeded,failed}`.
   - `subscription_status` field on `tenants` updated by webhook.
   - Subscription middleware: blocks access to all routes except `/billing` if `subscription_status` is `past_due` or `cancelled`.
5.2. **Signup flow**:
   - `/signup` → email + password → Stripe Checkout → callback creates tenant + admin user → redirect to `/setup` wizard.
   - Email verification via magic link (Resend or AWS SES).
5.3. **Master OAuth app setup** (operational, not code):
   - Submit Meta App for App Review (instagram_basic, instagram_content_publish, pages_manage_posts) — **this can take 2-4 weeks; start in Phase 2**.
   - Set up Google Cloud project for YouTube OAuth (no review needed for Shorts upload).
   - Submit TikTok app for audited mode (or ship with unaudited limits initially).
5.4. **Operator dashboard** (`/admin`, role=operator):
   - Tenant list with MRR, last-login, post count, subscription status.
   - Force-cancel, force-extend-trial, login-as-tenant (for support).
   - System-wide metrics (signups today, churn this month, total posts generated).
5.5. **Marketing site** (separate Next.js project or Framer):
   - Landing page with demo video.
   - Pricing page.
   - FAQ.
   - Trial signup CTA → routes to your Posty deploy's `/signup`.
5.6. **Tier enforcement**:
   - `tiers` table: `{slug, monthly_price, max_posts_per_month, max_social_accounts, allowed_models}`.
   - Pre-flight check before queueing a post; surface friendly error with upgrade CTA.
   - For v1 with one tier (~$29-49/mo): generous limits (e.g. 100 posts/mo, 3 accounts per platform, all models allowed).
5.7. **Email notifications**:
   - Trial ending in 2 days.
   - Trial converted / failed.
   - Post failed (digest, daily).
   - Monthly usage summary.
5.8. **Compliance basics**:
   - Terms of service + Privacy policy (boilerplate, customized).
   - Cookie banner if targeting EU.
   - Data export endpoint (GDPR-friendly).

**Deliverable**: Public SaaS live at your domain. Anyone can sign up, trial, pay, and use the product end-to-end.

---

## 10. Repository Reorganization

Today: everything sits at `tripavail_ai/` root. Going forward:

```
posty/                              # rename project root
├── apps/
│   ├── web/                        # FastAPI app
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── auth/
│   │   ├── oauth/
│   │   └── schemas/
│   ├── worker/                     # APScheduler runner
│   │   └── main.py
│   └── frontend/                   # Next.js app
│       ├── app/
│       ├── components/
│       └── lib/
├── core/                           # shared engine library (refactored from current core/)
│   ├── niche/
│   ├── topics/
│   ├── content/
│   ├── media/
│   ├── providers/                  # NEW — provider abstractions
│   ├── pipeline/
│   ├── scheduling/
│   └── social/                     # mostly empty after refactor; concrete posters live in providers/social/
├── db/
│   ├── models.py                   # SQLAlchemy
│   ├── alembic/
│   └── seeds/
├── templates/                      # Jinja2 prompt templates
├── tests/
├── docker/
│   ├── Dockerfile
│   └── entrypoint.sh
├── railway.toml
├── pyproject.toml
├── README.md                       # NEW user-facing readme
└── docs/                           # buyer-facing docs (Mintlify or GitHub Pages)
```

The current `tripavail_ai/` becomes a *legacy* directory we strangle out as Phases 1-2 complete. The 80+ `*.md` design docs at its root get archived to `docs/archive/`.

---

## 11. Locked Decisions

- **Dual-mode codebase**: Mode A (single-tenant license) + Mode B (multi-tenant SaaS), switched by `DEPLOYMENT_MODE` env. ✅
- **BYOK OpenAI in both modes**: users pay OpenAI directly via their own key, see spend in dashboard. ✅
- **SaaS pricing**: 7-day free trial → single tier (~$29-49/mo), no permanent free tier. ✅
- **Master OAuth apps (Mode B)**: you create one Meta/Google/TikTok app each; users one-click connect. ✅
- **Release order**: ship Mode A to Tashfeen first (~10 weeks), then Mode B SaaS launch (~4 weeks after). ✅

## 12. Locked Decisions (Phase 1 unblocked)

- **Product name**: Social Media Automation. ✅
- **Long video in MVP**: Included from day 1 as a length toggle. Existing tourism long-video logic gets generalized alongside the short-video flow. ✅
- **Repo**: Fresh repo at `D:\posty\social-media-automation\`. Clean slate. Salvage engine code from `tripavail_ai/`, drop everything tourism-specific. ✅
- **Tourism deploy**: Abandoned. Not in use, not being maintained. No backwards compatibility needed. ✅

---

## 12. Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Customer's OpenAI bill explodes from a runaway loop | High | Hard daily spend cap per provider in the worker; circuit-breaker after N failures. |
| TikTok / Meta API approval delays the product launch | High | Document the customer's app-creation steps clearly; ship without TikTok if approval blocks us, add it post-launch. |
| Customer's deploy gets banned on Instagram for spammy posting | Medium | Default rate limits in `posting_rules` (max N posts/day/platform). Surface warning if customer tries to override. |
| Customer can't figure out OAuth setup → support burden | High | Loom video for each platform + in-app inline help links + a "managed onboarding" upsell (you do the OAuth setup for them, charge $X). |
| Customer's video files fill the Railway volume | Medium | Keep current `auto_deletion.py` behavior (24h retention); make retention configurable. |
| One bad provider response (e.g. malformed Gemini image) crashes a job | Low | Try/except with dead-letter queue → surfaced in admin "failed" view with retry button. |
| Pivot underestimates frontend work | Medium | Phase 3 is the riskiest; plan a working-but-ugly version first, iterate on polish. |
| Existing 100+ planning docs in `tripavail_ai/` confuse you mid-rewrite | Medium | Archive them all to `docs/archive/` on day 1 of Phase 1. Out of sight, out of mind. |

---

## 13. Estimated Timeline

Optimistic, assuming one full-time developer (you + me):

| Phase | Duration | Cumulative |
|---|---|---|
| Phase 1 — Generalize engine + cost tracking | 2 weeks | Week 2 |
| Phase 2 — Backend with multi-tenancy baked in | 3 weeks | Week 5 |
| Phase 3 — Frontend (mode-aware) | 3-4 weeks | Week 9 |
| Phase 4 — Ship Mode A (Tashfeen) | 1-2 weeks | Week 11 |
| Phase 5 — Ship Mode B (SaaS launch) | 3-4 weeks | Week 15 |
| **Mode A live (Tashfeen)** | | **~Week 10-11** |
| **Mode B live (SaaS)** | | **~Week 14-15** |

Realistic with buffer (TikTok API surprises, Meta App Review delays for Mode B): **Mode A ~14 weeks, Mode B ~18 weeks**.

**Critical parallel track**: Submit Meta App Review during Phase 2, not Phase 5 — it takes 2-4 weeks of back-and-forth and is the biggest risk to Mode B launch.

---

## 14. What Happens Next

Once you greenlight this plan and answer the §11 questions:

1. I create a new branch (or fresh repo) with the Phase 1 directory layout.
2. Archive the current 80+ design `.md` files to `docs/archive/` so the root stays focused.
3. Build the provider abstraction layer first — this is the keystone, everything else depends on it.
4. Smoke-test with a non-tourism niche (e.g. "home cooking recipes") so we can prove the pivot works before any DB or web work.
5. Then move to Phase 2.

I'll write a separate, more detailed task breakdown for Phase 1 once you confirm.
