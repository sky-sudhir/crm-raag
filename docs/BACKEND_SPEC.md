# Backend Technical Specification — Multi‑Tenant Role‑Based RAG Platform

_Last updated: 2025-08-13 17:59:30Z (UTC)_

> **Purpose**: This document defines a production‑grade backend spec (APIs, business logic, data model, tenancy, auth, RAG flows, ops) so an implementation agent can build the system **without guesswork**.

---

## 0) Executive Summary

- **Platform**: Multi‑tenant, role‑based **RAG** SaaS with **PostgreSQL schema per client** and **pgvector** for embeddings. Originals stored in **Amazon S3**.
- **Tenancy**: Strong isolation per client via **dedicated Postgres schema**; global metadata in a shared public schema.
- **Access Control**: Role (admin/user) + Category‑based authorization; union of categories determines retrieval scope.
- **RAG Modes**: **Basic**, **Advanced**, **Customized** (per client; prompts & chunking strategies configurable).
- **Primary Stack (reference)**: Python 3.11+, **FastAPI** (async), SQLAlchemy 2.x, **pgvector**, asyncpg, Alembic, Redis + RQ/Celery (background), AWS S3, JWT, OpenTelemetry, Prometheus/Grafana, Sentry.
- **Security**: JWT, schema‑level isolation, least‑privilege IAM to S3, PII minimization, encryption at rest/in transit, audit logs, rate‑limits, request signing for uploads.

> The spec is language‑agnostic where sensible, but concrete examples target **FastAPI + PostgreSQL** to reduce ambiguity.

---

## 1) Service Layout

```
/app
  /api                 # FastAPI routers
    tenants.py         # onboarding/offboarding; schema ops
    auth.py            # login, token refresh, password reset
    users.py           # CRUD, role/category assignment
    categories.py      # CRUD
    documents.py       # upload, ingest, delete
    search.py          # RAG query endpoints
    logs.py            # audit & event logs
    health.py          # liveness/readiness/version
  /core
    config.py          # env, settings, feature flags
    db.py              # engine, session, schema routing
    security.py        # JWT, password hashing, RBAC guards
    s3.py              # presigned URLs, upload policies
    vector.py          # embedding utils, pgvector helpers
    chunking.py        # splitting strategies
    rag.py             # retrieval, ranking, prompting, LLM call
    tenants.py         # schema DDL helpers
    rate_limit.py      # per‑IP / per‑user limits
  /models              # SQLAlchemy models (public + tenant)
  /migrations          # Alembic (schema-templated)
  /workers             # background jobs (ingest, re-embed, deletes)
  /tests               # unit/integration/e2e tests
```

---

## 2) Configuration

- **ENV**: `APP_ENV`, `DATABASE_URL`, `JWT_SECRET`, `JWT_TTL`, `S3_BUCKET`, `S3_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `EMBEDDING_MODEL`, `MAX_UPLOAD_MB`, `ALLOWED_MIME`, `RATE_LIMIT_*`, `OTEL_*`, `SENTRY_DSN`.
- **Secrets** via vault/secret manager; **never in repo**.
- **Feature Flags**: `ENABLE_HYBRID_SEARCH`, `ENABLE_CUSTOM_PROMPTS`, `ENABLE_DOC_VIRUS_SCAN`.
- **Observability**: OTEL traces, structured logs (JSON), Prometheus metrics.

---

## 3) Data Model

### 3.1 Global (public schema)

- **clients**

  - `id UUID PK`
  - `name text unique`
  - `schema_name text unique`
  - `rag_type enum('basic','advanced','customized')`
  - `onboarded_at timestamptz default now()`
  - `status enum('active','suspended','deleted') default 'active'`
  - Index: `clients_name_key`, `clients_status_idx`

- **api_keys** (optional for server‑to‑server)
  - `id UUID PK`, `client_id FK`, `key_hash text`, `scopes text[]`, `created_at`, `revoked_at`

### 3.2 Per‑tenant schema (`{schema}`)

- **users**

  - `id UUID PK`, `name`, `email unique`, `password_hash`, `role enum('admin','user')`
  - `categories UUID[]` (denormalized cache) _and_ many‑to‑many via join table (source of truth)
  - `rag_type enum('basic','advanced','customized')`
  - `created_at`, `last_login_at`
  - Indexes: `users_email_key`, `users_role_idx`

- **categories**

  - `id UUID PK`, `name text unique`, `created_at`
  - Index: `categories_name_key`

- **user_categories** (M2M)

  - `user_id FK`, `category_id FK`, `PRIMARY KEY (user_id, category_id)`

- **document_files** (originals in S3)

  - `id UUID PK`, `category_id FK`, `s3_key text`, `filename`, `mime`, `size_bytes`
  - `metadata jsonb` (source, title, language, checksum, uploader_id, pages, etc.)
  - `status enum('uploaded','ingesting','ready','failed','deleted') default 'uploaded'`
  - `created_at`, `updated_at`, `deleted_at`
  - Indexes: `(category_id)`, `gin(metadata)`

- **vector_documents** (chunks for retrieval; pgvector)

  - `id UUID PK`, `category_id FK`, `file_id FK -> document_files.id`
  - `chunk_id int`, `chunk_text text`, `embedding vector(1536)`
  - `metadata jsonb` (page_no, section, author, chunker, version, language, etc.)
  - `created_at`
  - Indexes: `ivfflat(embedding) with (lists=100)`, `gin(metadata)`; co‑locate with `category_id`

- **chat_history**

  - `id UUID PK`, `user_id FK`, `question text`, `answer text`, `citations jsonb[]`
  - `latency_ms int`, `tokens_prompt int`, `tokens_completion int`
  - `created_at`
  - Index: `chat_history_user_id_created_at_idx`

- **logs**
  - `id UUID PK`, `user_id FK null`, `event_type enum('error','query','upload','embedding_creation','api_call')`
  - `details jsonb`, `created_at`
  - Index: `logs_event_type_idx`, `gin(details)`

**Constraints & Invariants**

- All tenant tables **only visible inside tenant schema**.
- `vector_documents.file_id` must reference a `document_files` with `status='ready'`.
- On category delete: deny if any `document_files` exist (soft delete first).

---

## 4) Tenancy & Routing

- Each client has schema: `tenant_{slug}`.
- DB connections use search*path = `tenant*{slug}`, public.
- **Request scoping**: Every request carries a **Client‑ID** (from JWT ). A dependency resolves to tenant schema and the current user id and binds a session with that `search_path`.
- **Onboarding**: create schema, run Alembic tenant migrations, bootstrap admin user.
- **Offboarding**: lock users, revoke API keys, export data, soft‑delete in public.clients, schedule S3 purge.

---

## 5) Authentication & Authorization

- **Auth**: Email+password → JWT (access). Password hashing with Argon2/bcrypt.
- **Claims**: `sub` (user_id), `client_id`, `role`, `rag_type`, `category_ids` (cached), `exp`.
- **RBAC**: Decorators/Deps enforce role and **category scope**: queries limited to assigned categories.
- **Admin Actions** (tenant): category CRUD, user CRUD, doc lifecycle, logs view.
- **User Actions**: chat, own history, read‑only document metadata in assigned categories.

**Edge Cases**

- Suspended client → all requests return `403 CLIENT_SUSPENDED`.
- User locked or password expired → `403 USER_LOCKED` / `401 PASSWORD_EXPIRED`.
- Category scope empty → `403 NO_CATEGORY_ACCESS`.

---

## 6) Document Lifecycle (S3 + Ingestion)

### 6.1 Upload

1. Client admin requests **presigned POST** for `/upload/{category}/{filename}`.
2. Frontend uploads directly to S3 with size/type policy.
3. Backend creates `document_files` row with `status='uploaded'` and enqueues `ingest` job.

**Validation**

- Allowed MIME (`pdf`, `docx`, `txt`, `md`, `pptx`, `xlsx` as configured).
- Size ≤ `MAX_UPLOAD_MB`.
- Deduplicate via file SHA256 (optional: reject duplicates or link to existing).

### 6.2 Ingest Job (worker)

- Download from S3 (stream), extract text per page/slide, normalize (lang detect, clean).
- **Chunking**: token‑aware; strategies per client (Basic/Advanced/Customized).
- Create embeddings → insert rows in `vector_documents` batched.
- Update `document_files.status='ready'` or `'failed'` with error details.
- Write `logs(event_type='embedding_creation')`.

**Edge Cases**

- Corrupt files → mark `failed`, include parser error.
- Empty content → reject with `EMPTY_CONTENT`.
- Very large files → split multi‑job; resume on retry; idempotent by `file_id + chunk_id`.

### 6.3 Delete

- Soft delete: set `deleted_at` on `document_files`, cascade logical delete to vectors.
- Hard purge: background job removes S3 object and vectors; write audit log.

---

## 7) Retrieval & Generation (RAG)

### 7.1 Query Pipeline

1. **Authorize**: ensure user has categories → get `category_ids`.
2. **Candidate Fetch**:
   - **Basic**: pure vector KNN within `category_ids`.
   - **Advanced**: **hybrid** (vector + BM25/pg_trgm), metadata filters (language, recency, file, category).
   - **Customized**: apply client‑provided **prompt template** and **chunking profile**; optional reranker.
3. **Ranking**: score fusion (e.g., reciprocal rank fusion) and diversity.
4. **Prompt Build**: system prompt + safety + citations.
5. **LLM Call**: with context window budget; stream tokens if needed.
6. **Post‑processing**: cite top chunks; redact PII if configured; guardrail checks.
7. **Persist**: save `chat_history` and `logs(event_type='query')` with metrics.

**Edge Cases & Guards**

- No results → return graceful fallback: “No confident answer”; include `top_k=0`.
- Hallucination guard: if confidence < threshold, return abstain with citations list empty.
- Over‑long prompts → truncate by token budget.
- Cross‑tenant leakage prevented by schema scoping and category filters.
- Disallowed content → policy filtered before LLM call; log `error` with code `CONTENT_BLOCKED`.

---

## 8) API Contract (v1)

Base URL: `/api/v1`

### 8.1 Auth

- `POST /auth/login`
  - Body: `{ email, password, client }`
  - 200: `{ access_token, refresh_token, user: {{id,name,role,rag_type,category_ids}} }`
  - 401: `INVALID_CREDENTIALS`, 403: `CLIENT_SUSPENDED`
- `POST /auth/refresh`
  - Body: `{ refresh_token }`
  - 200: `{ access_token }`
  - 401: `INVALID_REFRESH`

### 8.2 Tenants (platform ops)

- `POST /tenants`
  - Body: `{ name, slug, rag_type }`
  - Creates public.clients, schema, migrates, seeds admin.
- `POST /tenants/{client_id}/suspend` / `/activate`
- `GET /tenants/{client_id}` → metadata & health
- **Notes**: protected by platform API key & IP allowlist.

### 8.3 Users (tenant admin)

- `POST /users` → create (email invite optional)
- `GET /users` → list (pagination, filters: role, email)
- `GET /users/{id}`
- `PATCH /users/{id}` → update role, categories, rag_type
- `DELETE /users/{id}` → soft delete; can’t delete self if last admin
- Errors: `EMAIL_EXISTS`, `LAST_ADMIN_FORBIDDEN`

### 8.4 Categories (tenant admin)

- `POST /categories` `{ name }`
- `GET /categories`
- `PATCH /categories/{id}`
- `DELETE /categories/{id}`: 409 if documents exist

### 8.5 Documents

- `POST /documents/presign` (admin)
  - Body: `{ filename, mime, size_bytes, category_id }`
  - 200: `{ url, fields, s3_key, file_id }`
- `POST /documents/ingest/callback` (optional S3 event/webhook) → start job
- `GET /documents` (admin) → list by status/category; pagination
- `GET /documents/{id}` → metadata, status
- `DELETE /documents/{id}` → soft delete; schedules purge
- Errors: `MIME_NOT_ALLOWED`, `TOO_LARGE`, `CATEGORY_NOT_FOUND`

### 8.6 Search / Chat

- `POST /chat/query`

  - Body:
    ```json
    {
      "question": "...",
      "category_ids": ["..."],
      "top_k": 8,
      "filters": { "file_id": null, "mime": null, "recency_days": 365 },
      "mode": "basic|advanced|customized",
      "stream": false
    }
    ```
  - 200:
    ```json
    {
      "answer": "...",
      "citations": [
        { "file_id": "...", "s3_key": "...", "page": 3, "snippet": "..." }
      ],
      "metrics": {
        "latency_ms": 1234,
        "retrieved": 8,
        "used": 4,
        "confidence": 0.71
      },
      "guardrail": { "blocked": false, "reason": null }
    }
    ```
  - 400: `NO_CATEGORY_ACCESS`, 422: validation

- `GET /chat/history?user_id=&limit=&cursor=`
  - Returns stable cursor for pagination

### 8.7 Logs (tenant admin)

- `GET /logs?event_type=&q=&from=&to=&limit=&cursor=`
- `GET /logs/{id}`

### 8.8 Health & Info

- `GET /health/live` (200)
- `GET /health/ready` (checks DB, S3, workers, embedding provider)
- `GET /version` (git sha, build time, migration version)

**Common Response Wrapper**

```json
{
  "data": <payload|null>,
  "total_count": <int|null>,
  "message": "<ok|error reason>",
  "error": {"code": "STRING_CODE", "details": <object|null>}
}
```

---

## 9) Business Logic Rules (selected)

1. **Category Union**: Effective scope is the union of assigned categories. If none, deny queries.
2. **RAG Type Resolution**: Request mode defaults to `user.rag_type`, else `client.rag_type`. Admin can override per request (if allowed).
3. **Metadata Filters** (Advanced/Customized): Date windows, mime, file ids, languages; validated against user scope.
4. **Chunk Versions**: Re‑ingest of a file creates a new `version` in metadata; retrieval prefers latest version unless `filters.version` specified.
5. **Idempotency**: Upload/ingest/delete endpoints accept `Idempotency-Key` header. Duplicate calls return the original result.
6. **Rate Limits**: e.g., 60 req/min per user; 10 uploads/min per tenant; burst token bucket. Exceed → `429`.
7. **Retention**: No auto‑expiry; manual purge only (future policy can add TTL).
8. **Search Safety**: Disallow cross‑tenant joins; enforce `search_path` and never accept raw `schema` from client.
9. **Citations**: Always include file id + page when available; redact secrets by regex before storing history if PII redaction enabled.

---

## 10) Indexing & Performance

- **pgvector**: `ivfflat` with appropriate `lists` per table size (reindex after bulk loads).
- **Hybrid** (Advanced): `pg_trgm` on `chunk_text`, `GIN` on `metadata`.
- **Partitioning** (optional): by `category_id` or by month for `chat_history` and `logs`.
- **Connection Pooling**: pgbouncer transaction pooling (beware session SET search_path; use server‑side parameter).
- **Caching**: LRU cache for category id list per user; invalidate on user update.
- **Workers**: concurrency tuned to CPU for embedding rate; backoff/retry with dead‑letter queue.

---

## 11) Security & Compliance

- **JWT** with short TTL; refresh rotation; immediate revoke on password change.
- **S3**: presigned URLs with restricted content‑type/size; server‑side encryption (SSE‑S3/KMS).
- **DB**: TLS, at‑rest encryption; least privilege DB role per tenant app user if using separate roles.
- **PII**: Store minimal PII; hash emails for logs; secrets masked in logs.
- **Audit**: All admin actions logged with actor, timestamp, parameters hash.
- **Input Validation**: Pydantic models, max lengths, regex on filenames, strict enums.
- **Headers**: `X-Client-Id`, `Idempotency-Key`, `X-Request-Id`, `User-Agent`.
- **CORS**: restricted origins; `OPTIONS` properly handled.

---

## 12) Error Model (canonical)

- `CLIENT_SUSPENDED`, `INVALID_CREDENTIALS`, `INVALID_REFRESH`, `USER_LOCKED`, `NO_CATEGORY_ACCESS`
- `EMAIL_EXISTS`, `LAST_ADMIN_FORBIDDEN`, `CATEGORY_NOT_FOUND`, `CATEGORY_IN_USE`
- `MIME_NOT_ALLOWED`, `TOO_LARGE`, `EMPTY_CONTENT`, `INGEST_FAILED`, `OBJECT_NOT_FOUND`
- `RATE_LIMITED`, `CONTENT_BLOCKED`, `INTERNAL_ERROR`

All errors follow wrapper with `error.code` and optional `details` and a stable HTTP code.

---

## 13) Migrations & Seeding

- **Alembic** with two heads:
  - **public** head for global tables.
  - **tenant** head applied per schema during onboarding.
- **Onboarding Flow**:
  1. Insert into `public.clients`.
  2. Create schema `tenant_{slug}`.
  3. Run tenant head migrations.
  4. Create first admin user.
- **Rollback**: idempotent drops guarded; keep history in `alembic_version` per schema.

---

## 14) Testing Strategy

- **Unit**: services (chunking, security, vector math).
- **Integration**: DB with ephemeral schema per test, S3 localstack, embedding mocked.
- **E2E**: tenant onboarding → upload → ingest → query → logs.
- **Contract tests**: OpenAPI schema snapshots; ensure no breaking changes across versions.
- **Load tests**: K6/gatling profiles for search & ingest.

---

## 15) Deployment & Ops

- **Containers**: multi‑process (Uvicorn workers), separate worker deployment.
- **Health Probes**: `/health/live`, `/health/ready`.
- **Blue/Green or Canary**: migrate first; ensure backward compatibility.
- **Backups**: PITR enabled; S3 lifecycle policy; verify restores quarterly.
- **Metrics**: P95 latency by endpoint, ingest throughput, embedding queue depth, vector table size, RPS, error rate.
- **Alerts**: on 5xx spikes, queue backlog, ingest failures, RAG abstain > threshold.

---

## 16) OpenAPI & SDKs

- Provide machine‑readable OpenAPI 3.1.
- Auto‑generate minimal SDKs (TS/Python) for `/auth`, `/documents`, `/chat`, `/logs` with retry & idempotency helpers.

---

## 17) Non‑Functional Requirements

- **Scalability**: 1k tenants, 10M chunks total; 200 QPS read, 10 QPS ingest.
- **Availability**: 99.9% target; graceful degradation (e.g., fallback to vector‑only if hybrid index offline).
- **Latency**: P95 chat < 2.5s with warm caches (excluding provider latency).

---

## 18) Reference SQL Snippets

```sql
-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Example vector index
CREATE INDEX IF NOT EXISTS idx_vec_docs_embedding
ON vector_documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Trigram index for hybrid
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_vec_docs_trgm
ON vector_documents
USING gin (chunk_text gin_trgm_ops);
```

---

## 19) Example Guarded Query (FastAPI/SQLAlchemy)

```python
async def knn_search(session, user, q_embed, top_k, category_ids):
    # Ensures tenant search_path already set on session
    sql = """
      SELECT id, file_id, chunk_text,
             1 - (embedding <=> :q_embed) AS score
      FROM vector_documents
      WHERE category_id = ANY(:cat_ids)
      ORDER BY embedding <=> :q_embed
      LIMIT :top_k
    """
    return await session.execute(sql, {
        "q_embed": q_embed, "cat_ids": category_ids, "top_k": top_k
    })
```

---

## 20) Glossary

- **Chunk**: a small text span with its own embedding and metadata.
- **Hybrid Search**: combine dense (vector) and sparse (BM25/trigram) signals.
- **Schema per tenant**: isolated namespace for each client in Postgres.

---

## 21) Cut‑List & Future Work

- SSO/OAuth, category hierarchy, automatic log TTL, per‑client LLM isolation, semantic cache, virus scanning, human‑feedback analytics.
