# GuruPix — Data Architecture

This document describes the user login and data persistence flow, database schema, API coverage, and storage decisions. It matches the current implementation.

## Storage

- **Postgres**: All persistent user data (users, profiles, events, contexts, etc.)
- **Redis**: OAuth state (short-lived), rate limiting, session touch (sliding TTL). No user data is stored in Redis long-term.

## Database Schema

### Tables

| Table | Purpose | Key FKs |
|-------|---------|---------|
| `users` | User accounts (email, password_hash for email/password; OAuth links in oauth_accounts) | — |
| `oauth_accounts` | OAuth provider links (e.g. Google) | `user_id` → users.id (CASCADE) |
| `profiles` | User preferences, region, consent, embedding ref | `user_id` → users.id (CASCADE) |
| `items` | Catalog (movies, series, episodes) | — |
| `item_availability` | Where to watch per provider/region | `item_id` → items.id (CASCADE) |
| `item_reviews_agg` | Aggregate review scores per source | `item_id` → items.id (CASCADE) |
| `contexts` | Saved context presets (e.g. "date night") | `user_id` → users.id (CASCADE) |
| `events` | User feedback (like, dislike, watch_complete, skip, click) | `user_id` → users.id (CASCADE), `item_id` → items.id (CASCADE), `context_id` → contexts.id (SET NULL) |
| `context_events` | Log of context/vibe prompt usage | `user_id` → users.id (CASCADE), `context_id` → contexts.id (SET NULL) |
| `models` | Model registry (candidate/promoted) | — |

### Indexes

- `users`: `ix_users_email` (unique)
- `oauth_accounts`: `ix_oauth_accounts_user_id`, `ix_oauth_accounts_provider`, `ix_oauth_accounts_provider_account_id`, `uq_oauth_provider_account`
- `profiles`: PK on `user_id`
- `events`: `ix_events_user_id`, `ix_events_item_id`, `ix_events_type`, `ix_events_session_id`, `ix_events_request_id`, `ix_events_context_id`
- `contexts`: `ix_contexts_user_id`
- `context_events`: `ix_context_events_user_id`, `ix_context_events_context_id`

### Cascade Behavior

- Delete user → CASCADE deletes oauth_accounts, profiles, contexts, events, context_events
- Delete item → CASCADE deletes item_availability, item_reviews_agg, and events (events.item_id has CASCADE)
- Delete context → SET NULL on events.context_id, context_events.context_id

## Login → Persistence Flow

1. **User logs in** (email/password or Google OAuth)
   - Email/password: `POST /api/v1/auth/login` → JWT with `sub` = user_id
   - Google: `GET /auth/google/start` → `GET /auth/google/callback?code=&state=` → JWT
   - Signup: `POST /api/v1/auth/signup` → JWT
   - JWT stored in `localStorage` (`gurupix_token`) on frontend; sent as `Authorization: Bearer <token>`

2. **Profile created via onboarding**
   - `POST /api/v1/profiles/me` with `consent_data_processing: true` (required)
   - Or `PATCH /api/v1/profiles/me` when creating new profile — also requires `consent_data_processing: true`
   - Profile stored in Postgres

3. **Events recorded**
   - `POST /api/v1/events` with `item_id`, `type` (like, dislike, watch_complete, skip, click)
   - Optional: `context_id`, `metadata`
   - Stored in Postgres; `session_id` and `request_id` from middleware if present

4. **Contexts**
   - `POST/GET/DELETE /api/v1/contexts` for context presets
   - Tables `contexts` and `context_events` exist
   - Events can reference `context_id` when submitting feedback in a contextual session

## API Coverage

### Auth (`/api/v1/auth`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/signup` | Create email/password account → JWT |
| POST | `/login` | Authenticate → JWT |
| GET | `/me` | Current user (requires Bearer) |
| GET | `/google/start` | OAuth consent URL |
| GET | `/google/callback` | OAuth callback → JWT |

### Profiles (`/api/v1/profiles`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/me` | Get profile; returns `null` if not onboarded |
| POST | `/me` | Create profile (onboarding); requires `consent_data_processing: true` |
| PATCH | `/me` | Update or create profile; creating requires `consent_data_processing: true` |

### Events (`/api/v1/events`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `` | Record feedback (item_id, type, optional context_id, metadata) |

### Contexts (`/api/v1/contexts`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `` | Create context preset (label, attributes) |
| GET | `` | List user's context presets |
| DELETE | `/{context_id}` | Delete context (404 if not found or not owned) |

**Note**: `context_events` table logs context usage (e.g. when recommendations use a vibe prompt). No public API for context_events; created internally by recommendation flow.

## Edge Cases

| Scenario | Behavior |
|---------|----------|
| Invalid/expired token | 401, detail "Invalid or expired token" |
| Missing Authorization header | 401, detail "Missing or invalid Authorization header" |
| Missing profile | GET /profiles/me returns `null`; frontend should show onboarding |
| Invalid `item_id` on event | 404, detail "Item or context not found. Ensure item_id exists in catalog." |
| Invalid `context_id` on event | 404 (same IntegrityError handling) |
| Invalid event type | 422 (Pydantic validation) |
| POST profile without consent | 400, "You must accept data processing to continue" |
| PATCH creating profile without consent | 400, "You must accept data processing to create a profile" |

## Session / Token Handling

- **JWT**: Stored in `localStorage` under key `gurupix_token`
- **API client**: Attaches `Authorization: Bearer <token>` to requests
- **401 on protected endpoints**: Frontend clears token and redirects to `/login`
- **Session ID**: `X-Session-Id` header; echoed in response; optionally touched in Redis for sliding TTL
- **Request ID**: `X-Request-Id` on every request/response

## Migrations

- `001_initial_schema.py`: users, oauth_accounts, profiles, items, item_availability, item_reviews_agg, contexts, models, events, context_events
- `002_add_password_hash.py`: `password_hash` on users (nullable for OAuth-only users)
- `003_seed_admin_user.py`: Idempotent admin user seed

Run: `alembic upgrade head` from backend directory.
