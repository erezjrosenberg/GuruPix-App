# GuruPix — Bulletproof, Agent-Executable Build Roadmap
**DB + Redis + Google Login + Hooks/Middleware + “Where to Watch” + Contextual Vibes + AI-Profile Connector + Critics/Review Sources + Tracking/Privacy + CI/Test Gates**

**STATUS:** Authoritative plan to execute end-to-end.  
**AUDIENCE:** Human devs **and** AI coding agents.  
**GOAL:** Build GuruPix in staged, test-gated increments with clear “Definition of Done” per step.

---

## 0) Product Intent (Non-Negotiable Requirements)

GuruPix is a hyper-personalized movie & TV recommendation app that:

1) Ingests a catalog of movies/series/episodes into a canonical schema.  
2) Personalizes recommendations using:
   - onboarding quiz (cold start), and
   - ongoing feedback events (learning loop).
3) Supports **Google login** + email/password.
4) Uses **Postgres** for persistence + **Redis** for caching/rate limiting + **Qdrant** for embeddings.
5) Shows **where-to-watch** availability per region/providers.
6) Adds **contextual natural language prompting** for situations/moods/vibes (date night, family, falling asleep, etc.).
7) Lets users select **favorite critics / review sources** to tune ranking/explainability (e.g., Roger Ebert, NYT, Den of Geek, Rotten Tomatoes Critics, Rotten Tomatoes Audience).
8) Can optionally import “AI profile” preferences (consent-driven) via safe connectors (paste/import first; API integration later if supported).
9) Is scale-ready: modular services, hooks/event bus, middleware, model registry, experiments, analytics.
10) Includes **tests after every step** with regression guards.

---

## 1) System Overview (How It Works)

### 1.1 Runtime flow (user-facing)
1) User signs up/logs in (Email/Password or Google OAuth).
2) User completes onboarding quiz → profile is created.
3) User requests recommendations:
   - Standard: “Recommend for me”
   - Contextual: “Recommend for date night, cozy, not scary, under 2 hours”
4) Backend fetches candidates (vector search) → ranks them → attaches “why this” → attaches where-to-watch → attaches critic/review signals (when available/permitted).
5) User interacts (click/like/dislike/watch_complete/skip) → events stored → profile updates → cache invalidated.
6) Offline training periodically improves ranking → model registry → A/B rollout.

### 1.2 Core components
- **Frontend**: React app with hooks + API interceptors.
- **Backend**: FastAPI with middleware + internal hooks/event bus.
- **Storage**:
  - Postgres: users/profiles/items/availability/events/models/contexts/consents
  - Redis: caching, rate limit counters, optional session utilities
  - Qdrant: embeddings for similarity search
  - Optional MinIO: raw ingestion + artifacts

---

## 2) Repo Layout (Hard Contract)

```
/backend
  /app
    /api          # FastAPI routers
    /core         # config, settings, logging
    /db           # SQLAlchemy models + Alembic
    /middleware   # request-id, logging, timing, error, auth, rate-limit, cache, session
    /services     # profiles, recs, availability, ingestion, auth
    /hooks        # internal event bus + hook handlers
    /clients      # qdrant, redis, external APIs
    /schemas      # pydantic request/response contracts
    main.py
  /tests
    /unit
    /integration
  pyproject.toml

/frontend
  /src
    /pages or /routes
    /components
    /hooks
    /api          # API client + interceptors
    /state
    /tests
  package.json

/ml
  train.py
  embed.py
  evaluate.py
  /tests

/infra
  docker-compose.yml
  /k8s
  /terraform (optional)

/tests
  /e2e           # Playwright
  /load          # k6/locust fixtures

/docs
  ARCHITECTURE.md
  API.md
  DEVELOPER_GUIDE.md
  PRIVACY_AND_DATA.md
  RUNBOOKS.md
```

**Rule:** Any new module MUST fit this structure; no “misc” dumping.

---

## 3) Agent Operating Rules (Mandatory)

### 3.1 Step execution protocol (agent MUST follow)
For each checklist step:

1) Implement the change.
2) Add/adjust tests verifying expected behavior.
3) **Run required tests for that step** — run the relevant test suite (e.g. backend unit, backend integration) **after each checklist sub-step**, not only at the end of the stage. For example: after adding an endpoint, run unit tests; after adding middleware, run unit + integration; after adding a new test file, run it and the existing suite.
4) Write a short release note:
   - What changed
   - Tests run + results
   - Any relevant metrics or snapshots added/updated

### 3.2 Global “Definition of Done”
A step is DONE only if:
- Code compiles/builds
- Required tests pass
- Docs updated if the change impacts usage/contracts
- No regression guard violated

### 3.3 “Do Not Break Recommendations” policy
Any change touching recommendation logic MUST include:
- unit tests for new logic
- integration tests verifying output shape + deterministic ordering on tiny dataset
- regression snapshot OR metric guard threshold

### 3.4 Testing ladder (never skip)
- **Unit**: fast + deterministic.
- **Integration**: real Postgres/Redis/Qdrant via docker-compose.
- **E2E**: Playwright for core flows.
- **Model smoke**: tiny dataset training completes.

---

## 4) Data + Privacy Contract (What We Collect + Why)

### 4.1 Data categories
**Required for product to function**
- Account identity: email, auth provider, created_at
- Technical metadata: request_id, session_id, error logs (PII redacted)

**Required for continuous improvement**
- Behavioral events: clicks/likes/dislikes/watch_complete/skip (with timestamps + item_id)

**User-provided preferences**
- Quiz answers, explicit likes/dislikes, language/region/providers
- **Favorite critics / review sources preference** (see 4.3)

**Context prompting (potentially sensitive)**
- Vibe prompt text **may contain personal info**
- Default policy:
  - store parsed attributes + constraints
  - store raw prompt text only if user opts-in
  - redact obvious PII patterns before storage (best-effort)

**Optional connectors**
- Watch history imports, AI profile imports, etc. → only with explicit consent, revocable

### 4.2 User rights (must exist in MVP)
- Export my data
- Delete my data
- Toggle prompt retention
- Remove imported connector data

### 4.3 Review/critic data: legality + scope
- Only ingest/compute review signals that are **licensed or permitted** for your use case.
- Prefer:
  - official/partner APIs,
  - permitted datasets,
  - user-entered preferences (e.g., “I trust Ebert-style reviews”) without storing prohibited text.
- Avoid:
  - scraping restricted sites,
  - storing full review text unless explicitly licensed.

---

## 5) Environment + Local Dev (Hard Requirement)

### 5.1 docker-compose services
- Postgres
- Redis
- Qdrant
- (Optional) MinIO

### 5.2 Commands
- Infra: `docker-compose up -d`
- Backend: `cd backend && uvicorn app.main:app --reload`
- Frontend: `cd frontend && npm run dev`
- Backend unit: `cd backend && pytest tests/unit`
- Backend integration: `cd backend && pytest tests/integration`
- Frontend unit: `cd frontend && npm test`
- E2E: `cd tests/e2e && npx playwright test`
- Model smoke: `cd ml && python train.py --smoke`

### 5.3 App domain (GuruPix)
- **Production domain:** The app is intended to run at **www.gurupix.com**.
- Backend and frontend config (e.g. `.env`, env vars, or app config) MUST support:
  - **Allowed origins / CORS:** `https://www.gurupix.com` (and optionally `https://gurupix.com` if redirect is used).
  - **Base URL / API URL:** Backend base URL and frontend `VITE_API_URL` (or equivalent) set for `https://www.gurupix.com` (or API subdomain if used).
- OAuth (Google) redirect URIs must include `https://www.gurupix.com` (and any auth callback paths).
- Local dev can use `localhost`; production builds and deploy must use the www.gurupix.com domain.

---

# STAGED ROADMAP (Actionable + Test-Gated)

## STAGE 0 — Repo Bootstrap + CI + Contracts (Day 1)
**Goal:** A working skeleton with CI gating and documented contracts.

### 0.1 Create repo skeleton + docs
**Action**
- Create required directories.
- Add docs:
  - `/docs/ARCHITECTURE.md` (this plan summarized + diagrams later)
  - `/docs/API.md` (endpoint contract table)
  - `/docs/DEVELOPER_GUIDE.md` (setup + tests + env)
  - `/docs/PRIVACY_AND_DATA.md` (data contract, rights, retention)
- Add `.env.example` (backend/frontend), `docker-compose.yml`.

**Tests**
- CI runs: backend lint, frontend lint, unit placeholders.

**Done when**
- `docker-compose up -d` works
- CI is green

---

### 0.2 CI pipeline (merge gating)
**Action**
Add GitHub Actions jobs:
1) lint (backend+frontend)
2) unit tests (backend+frontend)
3) integration tests (compose)
4) e2e tests (Playwright)
5) model smoke tests
6) security scan

**Tests**
- PR triggers full pipeline.

**Done when**
- Branch protection: cannot merge if any job fails.

---

### 0.3 Pre-commit hooks
**Action**
- Backend: ruff, black, mypy, pytest unit
- Frontend: eslint, prettier, vitest

**Tests**
- `pre-commit run --all-files`

**Done when**
- Bad commits blocked locally + in CI.

---

## STAGE 1 — Backend Foundation + Middleware (Day 2–3)
**Goal:** A stable FastAPI base with consistent behavior.

### 1.1 FastAPI skeleton + health/version
**Action**
- `GET /health` → `{ "status": "ok" }`
- `GET /version` → `{ "version": "<git sha or semver>" }`

**Middleware (must implement)**
- RequestIdMiddleware (`X-Request-Id` generated if missing)
- LoggingMiddleware (structured logs include request_id, path, status, duration)
- TimingMiddleware (`X-Response-Time-ms`)
- ErrorMiddleware (standard error shape)

**Tests**
- Unit: schema + 200 status
- Integration: `/health` reachable via compose

**Done when**
- All middleware active and tested.

---

## STAGE 2 — Database + Migrations (Day 3–4)
**Goal:** Postgres schema is real, migrated, and testable.

### 2.1 DB models + Alembic migrations
**Action**
Create tables:

**Auth**
- `users` (id, email unique, created_at)
- `oauth_accounts` (id, user_id FK, provider, provider_account_id, email, tokens_metadata JSON, created_at)

**Profiles**
- `profiles` (user_id PK/FK, preferences JSON, embedding_id, region, languages[], providers[], consent JSON, created_at, updated_at)

**Catalog**
- `items` (id, type, title, synopsis, genres[], cast JSON, crew JSON, runtime, release_date, language, metadata JSON, created_at, updated_at)

**Availability**
- `item_availability` (id, item_id FK, provider, region, url, availability_type, updated_at)

**Review signals (optional, but schema-ready early)**
- `item_reviews_agg` (id, item_id FK, source, score, scale, last_updated, metadata JSON)
  - examples:
    - `source = "RT_CRITICS"`, score 0-100
    - `source = "RT_AUDIENCE"`, score 0-100
    - `source = "NYT"`, score 0-5 (example)
  - `metadata` can store confidence/attribution without storing prohibited content

**Learning loop**
- `events` (id, user_id, item_id, type, timestamp, session_id, request_id, context_id nullable, metadata JSON)

**Models**
- `models` (id, version unique, metrics JSON, status enum(candidate/promoted), created_at)

**Context prompts**
- `contexts` (id, user_id, label, attributes JSON, created_at)
- `context_events` (id, user_id, context_id nullable, timestamp, prompt_text nullable, parsed JSON, retention_opt_in bool, metadata JSON)

**Tests**
- Integration: `alembic upgrade head` from empty DB
- Integration: insert/select smoke for each table

**Done when**
- Migration runs clean from scratch in CI.

---

## STAGE 3 — Redis (Cache + Rate Limit + Session) (Day 4–5)
**Goal:** Redis is wired and enforced.

### 3.1 Redis integration
**Action**
- Add Redis config + client.
- Implement:
  - RateLimitMiddleware (per IP + per route key)
  - SessionMiddleware (ensure `session_id`)
  - Cache utilities (namespaced keys + TTL)

**Tests**
- Integration: rate limiting triggers after N requests
- Integration: responses include session_id header or body field as designed

**Done when**
- Redis is required in integration tests and passes.

---

## STAGE 4 — Authentication (Email/Password + Google OAuth) (Day 5–7)
**Goal:** Secure login, protected endpoints, and Google one-click login.

### 4.1 Email/password auth
**Action**
- `POST /auth/signup`
- `POST /auth/login`
- Choose ONE:
  - JWT bearer tokens, OR
  - Session cookie
- Implement AuthMiddleware:
  - validates token/cookie
  - attaches `user_id` to request context

**Tests**
- Unit: password hashing + token validation
- Integration: protected endpoint 401 without token, 200 with token

**Done when**
- Auth is stable and fully tested.

---

### 4.2 Google OAuth login (REQUIRED)
**Action (Backend)**
- `GET /auth/google/start`
- `GET /auth/google/callback`
- Validate `state` and CSRF
- Mock token exchange in tests
- Create/link user in `users` + `oauth_accounts`
- Return app auth token/session

**Action (Frontend)**
- Add “Continue with Google”
- Handle callback → store token → redirect

**Tests**
- Unit: state validation
- Integration: mocked token exchange creates/links user
- E2E: mocked OAuth flow works
- Regression: email/password remains working

**Done when**
- OAuth works in dev + tests.

---

## STAGE 5 — Catalog + Ingestion + Availability + Review Signals (Week 2)
**Goal:** Items exist, availability works, and review sources are wired safely.

### 5.1 Canonical item schema + validation
**Action**
- Pydantic schemas for items (movie/series/episode)
- Validation + normalization rules

**Tests**
- Unit: sample item fixtures validate
- Integration: insert/select canonical item

---

### 5.2 Seed ingestion (admin-only)
**Action**
- `POST /ingest/items` (admin-protected)
- Parse `/data/seed/` → canonical → DB
- Store raw payload (JSON column or MinIO)

**Hook**
- `on_item_ingested(item_id)` → enqueue vectorization

**Tests**
- Unit: parser correctness
- Integration: ingest seed yields expected count

---

### 5.3 “Where to Watch” availability
**Action**
- Dev: mock dataset loader populates `item_availability`
- API:
  - `GET /availability?item_id=...&region=...`
- Profile stores:
  - region + providers

**Filtering rule**
- Only show providers available in user region
- If user has provider preferences, rank them first

**Tests**
- Unit: filtering logic
- Integration: endpoint returns provider list + URLs
- E2E: UI displays where-to-watch on cards

---

### 5.4 Review signals ingestion (legal-first, MVP-safe)
**Purpose**
Let the product incorporate trusted sources without violating terms.

**Action**
- Implement a **mock review aggregator** in dev:
  - load `item_reviews_agg` from a permitted seed file
- Add API (read-only):
  - `GET /reviews/aggregate?item_id=...` → list of sources + scores
- In the UI:
  - show “Scores from: RT Critics / RT Audience / NYT …” when present
  - do NOT display full review text unless licensed

**Tests**
- Unit: review aggregation schema validation
- Integration: reviews endpoint returns expected sources for seeded item

---

## STAGE 6 — Profiles + Onboarding + Frontend Hooks (Week 2–3)
**Goal:** Users have persistent profiles + preferences including critics sources.

### 6.1 Profile CRUD + export/delete
**Action**
- `POST /profiles` (from onboarding)
- `GET /profiles/me`
- `PATCH /profiles/me`
- `DELETE /profiles/me`
- `POST /profiles/me/export`

**Add to profile fields**
- `favorite_review_sources[]` (strings/enum)
  - examples:
    - `Ebert`
    - `NYT`
    - `DenOfGeek`
    - `RT_Critics`
    - `RT_Audience`

**Hooks**
- `on_profile_created`
- `on_profile_updated` → invalidate cache keys

**Tests**
- Integration: CRUD + export includes favorite_review_sources
- Privacy: delete removes/anonymizes required data

---

### 6.2 Onboarding quiz (includes critics preference)
**Action**
- Frontend onboarding collects:
  - favorites, genres, cast/crew, tone, dislikes/triggers
  - region/providers/languages
  - **favorite critics / review sources** (multi-select)
- Backend maps → profile + embedding seed

**Frontend hooks (must exist)**
- `useAuth`, `useProfile`, `useOnboarding`

**Frontend API middleware**
- attach token + request-id
- normalize errors
- handle 401
- retry transient failures

**Tests**
- Unit: mapping logic includes favorite_review_sources
- E2E: login → onboarding → recs page

---

## STAGE 7 — Contextual “Vibes” Prompting (Week 3)
**Goal:** Users request recs by circumstance/mood with deterministic behavior.

### 7.1 Context model + parsing
**Action**
- Endpoints:
  - `POST /contexts/parse` → returns `{attributes, constraints}`
  - `POST /recommendations/contextual` → uses prompt/context
- Deterministic parser V1:
  - keyword maps (mood/setting/attention/pace)
  - constraint extraction (max_runtime, exclude_genres, rating_ceiling, etc.)
- Store context event:
  - parsed JSON always
  - raw prompt text only if retention opt-in
- Allow saving preset contexts:
  - `POST /contexts`
  - `GET /contexts`
  - `DELETE /contexts/{id}`

**Tests**
- Unit: fixture prompts parse deterministically
- Integration: contextual request respects constraints

**Done when**
- Contextual recs are stable and test-guarded.

---

## STAGE 8 — Recommendations + Caching + Explainability (Week 3–4)
**Goal:** Personalized ranking works, explainability exists, and caching is correct.

### 8.1 Embeddings + Qdrant baseline
**Action**
- Create Qdrant collections
- Embed items (synopsis + metadata)
- Store embedding_id reference

**Hook**
- `on_item_vectorized(item_id, vector_id)`

**Tests**
- Integration: known neighbors returned for fixture items

---

### 8.2 Recommendations endpoint (baseline)
**Action**
- `GET /recommendations?limit=&filters=`
- Retrieval:
  - user embedding → vector search → candidates
- Ranking includes:
  - similarity
  - genre boosts
  - recency preference
  - provider availability boosts
  - **context match boosts** (if contextual)
  - **review/critic preference boosts**:
    - if user prefers `RT_Critics`, items with high RT critics score get a positive bump
    - if user prefers `RT_Audience`, items with high audience score get a bump
    - if user prefers a named source, boost items that have that source score available
  - (Optional) “avoid low-score from preferred sources” as a soft penalty

**Response includes**
- `items[]` with:
  - `reason_snippet`
  - `confidence`
  - `availability[]`
  - `review_signals[]` (subset relevant to the user, or top sources)

**Redis caching**
- Cache key: `(user_id, filters, model_version, context_hash, review_pref_hash)`
- Invalidate on:
  - profile update
  - feedback received
  - model promoted

**Tests**
- Unit: deterministic ranking on fixed fixture inputs including review signals
- Integration: stable top list for tiny dataset
- Regression snapshot: top-N expected list locked (with and without review prefs)

---

### 8.3 Explainability endpoint
**Action**
- `GET /recommendations/{item_id}/explain`
- Must return ≥2 signals, and should include review-based reasons when relevant:
  - genre match
  - similarity to favorite
  - cast overlap
  - provider match
  - context match
  - **review source match** (e.g., “Strong Rotten Tomatoes Critics score (your preferred source)”)

**Tests**
- Unit: explanation includes required signals
- E2E: explanation modal renders

---

## STAGE 9 — Feedback + Events + Online Updates (Week 4)
**Goal:** Learning loop closes and affects future results.

### 9.1 Feedback endpoint + events
**Action**
- `POST /recommendations/{item_id}/feedback`
- Store events with:
  - user_id, item_id, type, timestamp, session_id, request_id
  - context_id/context_hash if applicable
  - review_pref_hash optional (for analysis)

**Hooks**
- `on_feedback_received`:
  - update profile stats (weights)
  - invalidate caches
  - enqueue training data

**Tests**
- Integration: feedback inserts event
- E2E: like/dislike updates UI and persists

---

### 9.2 Online profile update effect
**Action**
- Update preference weights and optionally embedding version
- Ensure audit trail (embedding version increments)

**Tests**
- Integration: feedback changes profile and impacts next recommendations

---

## STAGE 10 — Offline Training + Model Registry + A/B Testing (Week 4–6)
**Goal:** Safe model iteration with regression guards.

### 10.1 Training pipeline
**Action**
- `ml/train.py`:
  - read items + events + review signals (aggregate scores only)
  - engineer features (including context features + review-source preference features)
  - train ranker
  - evaluate NDCG@10, MAP, MRR
  - write artifact + metrics

**Model registry (DB)**
- create model row with version + metrics + status

**Tests**
- Smoke: tiny training completes
- Guard: metrics cannot drop below baseline threshold

---

### 10.2 Online serving + experiments
**Action**
- Stable bucketing on `user_id`
- Route:
  - baseline vs candidate
- Log assignment on each recommendation request

**Tests**
- Integration: stable routing
- Regression: output schema valid for both models

---

## STAGE 11 — Tracking + Dashboards + Admin Tools (Week 5–7)
**Goal:** Observability, product analytics, operational controls.

### 11.1 Metrics
**Action**
Track:
- CTR, watch-through, time-to-first-watch
- retention D1/D7/D30
- error rate, p95 latency
- model deltas + experiment deltas
- context adoption + satisfaction delta
- **review preferences usage** (e.g., how often review-based boosts correlate with positive feedback)

**Tests**
- Integration: metrics counters increment

---

### 11.2 Admin dashboard (role-protected)
**Action**
- Admin views:
  - ingestion status
  - model versions + metrics
  - A/B results
  - availability update status
  - review signals ingestion status
  - redacted user debug

**Tests**
- E2E: admin works
- Security: non-admin blocked

---

## STAGE 12 — AI Profile Connector (Optional, Consent-Driven) (Week 6+)
**Goal:** Import preference insights from a user’s external “AI profile” safely.

### 12.1 MVP-safe connector
**Action**
- Settings UI:
  - user pastes a preference summary OR uploads a file
  - preview extracted preferences (including critic preferences if detected)
  - user edits/approves
- Backend:
  - `POST /connectors/ai-profile/import`
  - `DELETE /connectors/ai-profile` (full removal)
- Store provenance + consent

**Tests**
- Unit: extraction deterministic
- Integration: imported prefs alter recommendations
- Privacy: delete removes imported data

**Note**
Do NOT claim to read private ChatGPT history automatically. If a future provider API exists, add it later behind explicit consent + security review.

---

## STAGE 13 — Production Hardening (Week 6+)
**Goal:** Deployment, performance, privacy compliance.

### 13.1 Load/perf
**Action**
- Tune caching
- Precompute hot lists
- Pagination + async loading

**Tests**
- Load tests meet SLO targets

### 13.2 Deploy
**Action**
- Dockerize services
- k8s manifests + HPA + limits
- **Domain:** Configure production to serve the app at **www.gurupix.com** (DNS, TLS, reverse proxy / ingress, and app CORS + base URL as in §5.3).
- Canary rollout: 10% → 50% → 100% + rollback

**Tests**
- staging smoke + e2e
- Production URL (www.gurupix.com) serves app and API as expected

### 13.3 Privacy compliance
**Action**
- Export + delete verified
- retention documented
- consent logs
- PII redaction enforced in logs

**Tests**
- deletion proof tests (profile + events + embeddings refs removed/anonymized)
- prompt retention toggle tests
- connector deletion tests

---

# Required Middleware + Hooks (Implementation Targets)

## Backend Middleware
- RequestIdMiddleware
- LoggingMiddleware
- TimingMiddleware
- ErrorMiddleware
- AuthMiddleware
- RateLimitMiddleware (Redis)
- SessionMiddleware
- CacheMiddleware (Redis)

## Backend Hooks (internal event bus)
- on_user_logged_in
- on_item_ingested
- on_item_vectorized
- on_profile_created
- on_profile_updated
- on_feedback_received
- on_cache_invalidate
- on_model_promoted
- on_availability_updated
- on_context_parsed
- on_context_used_for_recommendations

## Frontend Hooks
- useAuth
- useProfile
- useOnboarding
- useRecommendations
- useFeedback
- useExperimentBucket
- useContextPrompt

---

# MVP Checklist (Ship Criteria)

MVP is complete when ALL are true:
- Email/password login works
- Google login works
- Onboarding creates persistent profile including favorite critics/review sources
- Recommendations are personalized + explainable
- Feedback loop updates future recommendations
- Where-to-watch appears using region/providers
- Contextual vibe prompting influences recommendations (deterministic V1)
- Review source preference influences ranking/explainability (aggregate scores only; legal-first)
- Postgres + Redis + Qdrant run locally via docker-compose
- CI gates: lint + unit + integration + e2e + model smoke are green
- Export/delete + prompt retention toggle exist
- Architecture cleanly supports expansion (connectors + new models + new providers + new review sources)

---

# Agent Deliverables per Stage (Hard Output Requirements)

For EACH stage, the agent must produce:
1) Code changes
2) Test changes
3) “How to run” update in docs if needed
4) Release note entry (in PR description or `/docs/CHANGELOG_DEV.md`)

---

# Guardrails (Make It Bulletproof)

- No stage may introduce new endpoints without:
  - schema definitions (request/response)
  - unit tests for schema validation
  - integration test for happy path
- No recommendation changes without:
  - deterministic fixture dataset
  - regression snapshot lock
- No new data collection without:
  - update to `/docs/PRIVACY_AND_DATA.md`
  - export/delete compatibility
  - consent toggle if optional/sensitive
- No review/critic ingestion without:
  - documented source permission/licensing status
  - storing **aggregate scores only** by default (no full review text unless licensed)
