# GuruPix — Architecture Overview

This document summarizes the system design and component layout. See `ROADMAP_GuruPix_System_Design.md` for the full staged roadmap.

## Product Intent

GuruPix is a hyper-personalized movie & TV recommendation app that:

- Ingests a catalog of movies/series/episodes into a canonical schema
- Personalizes recommendations using onboarding quiz (cold start) and ongoing feedback (learning loop)
- Supports **Google login** + email/password
- Uses **Postgres** (persistence), **Redis** (caching/rate limiting), **Qdrant** (embeddings)
- Shows **where-to-watch** availability per region/providers
- Adds **contextual natural language prompting** (date night, family, falling asleep, etc.)
- Lets users select **favorite critics / review sources** for ranking/explainability
- Can optionally import “AI profile” preferences (consent-driven)
- Is scale-ready: modular services, hooks/event bus, middleware, model registry, experiments, analytics
- Includes **tests after every step** with regression guards

## Runtime Flow (User-Facing)

1. User signs up/logs in (Email/Password or Google OAuth).
2. User completes onboarding quiz → profile is created.
3. User requests recommendations (standard or contextual “vibes”).
4. Backend fetches candidates (vector search) → ranks → attaches “why this”, where-to-watch, critic/review signals.
5. User interacts (click/like/dislike/watch_complete/skip) → events stored → profile updates → cache invalidated.
6. Offline training periodically improves ranking → model registry → A/B rollout.

## Core Components

| Component   | Tech / Role                                                                 |
|------------|-----------------------------------------------------------------------------|
| **Frontend** | React app with hooks + API interceptors                                    |
| **Backend**  | FastAPI with middleware + internal hooks/event bus                         |
| **Postgres** | Users, profiles, items, availability, events, models, contexts, consents   |
| **Redis**    | Caching, rate limit counters, optional session utilities                   |
| **Qdrant**   | Embeddings for similarity search                                           |
| **MinIO**    | Optional: raw ingestion + artifacts                                         |

## Repo Layout (Hard Contract)

```
/backend     — FastAPI app (api, core, db, middleware, services, hooks, clients, schemas)
/frontend    — React app (pages, components, hooks, api, state, tests)
/ml          — train.py, embed.py, evaluate.py, tests
/infra       — docker-compose.yml, k8s, terraform (optional)
/tests       — e2e (Playwright), load (k6/locust)
/docs        — ARCHITECTURE.md, API.md, DEVELOPER_GUIDE.md, PRIVACY_AND_DATA.md, RUNBOOKS.md
```

Any new module MUST fit this structure; no “misc” dumping.

## Backend Middleware (Targets)

- RequestIdMiddleware, LoggingMiddleware, TimingMiddleware, ErrorMiddleware  
- AuthMiddleware, RateLimitMiddleware (Redis), SessionMiddleware, CacheMiddleware (Redis)

## Backend Hooks (Internal Event Bus)

- on_user_logged_in, on_item_ingested, on_item_vectorized  
- on_profile_created, on_profile_updated, on_feedback_received  
- on_cache_invalidate, on_model_promoted, on_availability_updated  
- on_context_parsed, on_context_used_for_recommendations  

## Frontend Hooks (Targets)

- useAuth, useProfile, useOnboarding, useRecommendations  
- useFeedback, useExperimentBucket, useContextPrompt  

## Testing Ladder

- **Unit**: fast + deterministic  
- **Integration**: real Postgres/Redis/Qdrant via docker-compose  
- **E2E**: Playwright for core flows  
- **Model smoke**: tiny dataset training completes  

Diagrams (sequence, deployment) can be added in later iterations.
