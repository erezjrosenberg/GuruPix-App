# GuruPix — Privacy and Data

Data contract, user rights, and retention. No new data collection without updating this doc and ensuring export/delete compatibility.

## Data Categories

### Required for product to function

- **Account identity**: email, auth provider, created_at  
- **Technical metadata**: request_id, session_id, error logs (PII redacted)

### Required for continuous improvement

- **Behavioral events**: clicks, likes, dislikes, watch_complete, skip (timestamps + item_id)

### User-provided preferences

- Quiz answers, explicit likes/dislikes, language, region, providers  
- **Favorite critics / review sources preference**

### Context prompting (potentially sensitive)

- Vibe prompt text **may contain personal info**  
- **Default policy**:
  - Store parsed attributes + constraints  
  - Store raw prompt text **only if user opts in**  
  - Redact obvious PII patterns before storage (best-effort)

### Optional connectors

- Watch history imports, AI profile imports, etc. → **only with explicit consent**, revocable

## User Rights (MVP)

- **Export my data** — full export of account, profile, events (as permitted by policy)  
- **Delete my data** — account and associated data removed/anonymized  
- **Toggle prompt retention** — control whether raw vibe prompt text is stored  
- **Remove imported connector data** — revoke and delete AI profile / imported history

## Review / Critic Data

- Only ingest or compute review signals that are **licensed or permitted** for our use case.  
- Prefer: official/partner APIs, permitted datasets, user-entered preferences (e.g. “I trust Ebert-style reviews”) without storing prohibited text.  
- Avoid: scraping restricted sites; storing full review text unless explicitly licensed.  
- Store **aggregate scores only** by default (no full review text unless licensed).

## Retention and Compliance

- Retention periods and legal bases will be documented here as the product is implemented.  
- Any new data collection must be added to this document and must support export and delete.
