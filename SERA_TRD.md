SERA — Technical Requirements Document (TRD)
Engineering Specification for Implementation
Audience: Backend/Frontend/ML engineers, DevOps, and any coding agent implementing SERA. Relationship to PRD: The Master PRD (SERA_Master_PRD.md) defines what and why. This document defines how — exact stack, schema, API contracts, repo layout, and infra — at the level a staff engineer would hand to a team on day one. Posture: This system handles regulatory and evidentiary data for SEBI-regulated financial institutions. It is engineered to the same bar as core fintech infrastructure — correctness and auditability take priority over developer convenience or raw speed at every decision point below.

Table of Contents
Engineering Principles
Final Tech Stack & Decision Rationale
Repository Structure (Monorepo)
Database Architecture
Vector Database & Retrieval Architecture
API Architecture
Backend Service Architecture
AI Orchestration Layer (LangGraph)
Event Bus & Background Processing
Frontend Architecture
Authentication, Authorization & Multi-Tenancy
Infrastructure & Deployment
Security & Compliance Requirements
Testing Strategy
Observability & SRE
Non-Functional Requirements / SLAs
Environment & Configuration Reference
Appendix: Naming & Coding Conventions

1. Engineering Principles
These are non-negotiable, in priority order:
Postgres is the single source of truth. No durable state — including vectors and the Shared Workflow Document (SWD) — lives outside Postgres unless explicitly justified (e.g., large binary files in object storage, referenced by row).
Every mutation is attributable and reversible in record (not necessarily in effect). Nothing is a hard delete; everything is soft-deleted or versioned. The audit_log table is append-only at the database level (no UPDATE/DELETE grants for the app role).
AI output is data, not code. LLM output is always structured (JSON schema-validated) before it touches the database. Free-text LLM output never drives control flow directly.
Idempotency by default. Every state-mutating API call that could plausibly be retried (uploads, task creation, workflow advancement) requires an idempotency key.
Tenant isolation is enforced at the database layer (RLS), not just the application layer. Application bugs must not be able to leak cross-tenant data.
Every service is independently deployable and independently testable. No shared mutable in-process state between services.
Fail closed. If the Workflow Service cannot confirm a write to the SWD, downstream agents must not proceed.

2. Final Tech Stack & Decision Rationale
Layer
Choice
Version (baseline)
Why
Language (backend)
Python
3.12
Best-in-class LLM/RAG tooling (LangGraph, LangChain, Anthropic/OpenAI SDKs), async support via FastAPI
API framework
FastAPI
0.115+
Async-native, Pydantic v2 validation, auto OpenAPI generation used to drive both docs and frontend type generation
Data validation
Pydantic v2
2.x
Shared schema layer between API contracts and internal service boundaries; also used to validate LLM structured output
ORM / DB access
SQLAlchemy 2.0 (async) + Alembic
2.x
Explicit control over SQL for  RLS-sensitive queries; Alembic for reviewable, versioned migrations
Primary database
PostgreSQL
16
ACID, JSONB (for the SWD), native Row-Level Security, mature ecosystem
Vector extension
pgvector
0.7+
Keeps vectors transactionally consistent with the row they describe; avoids running/operating a second database (see §5 for the explicit build-vs-buy decision)
Object storage
Amazon S3 (prod) / Garage(local & CI)
—
Circulars, evidence files, exports; S3-compatible API keeps local/prod parity
Cache / broker
Redis 7
—
Celery broker, rate limiting, short-TTL caching (dashboard aggregates), pub/sub for real-time notification delivery
Task queue
Celery (+ Redis backend)
5.x
Mature, widely operated, supports scheduled + retryable jobs (recurrence, escalation sweeps, re-embedding)
AI orchestration
LangGraph
latest stable
Native checkpointing (backed by Postgres via langgraph-checkpoint-postgres), graph-based multi-agent control matches the SWD's stage model exactly
LLM provider
Claude (Sonnet-class) via Anthropic API, GPT-5-class as fallback provider
—
Structured-output support, tool use, strong long-context reasoning for legal text; dual-provider for resilience, not for quality-shopping
Embeddings
text-embedding-3-large (OpenAI) or Voyage/Cohere equivalent
—
3072-dim, strong retrieval benchmarks for legal/financial text; abstracted behind an EmbeddingProvider interface so it's swappable
Frontend framework
Next.js (App Router)
15.x
Server components for dashboard-heavy pages, streaming for AI-pipeline status
Frontend language
TypeScript
5.x
Type-safe API contract enforcement via OpenAPI-generated client
UI styling
Tailwind CSS + shadcn/ui primitives
—
Fast, consistent, accessible components; no heavyweight design system dependency
API client (frontend)
openapi-typescript-codegen generated client
—
Frontend types are generated from the backend's OpenAPI spec — contract drift becomes a build failure, not a runtime bug
Auth
JWT (access + refresh) issued by backend; OAuth2/OIDC + SAML SSO for enterprise tenants
—
JWT for service-to-service and SPA sessions; OIDC/SAML federation for enterprise IT requirements
Containerization
Docker
—
Standard
Orchestration
Kubernetes (EKS/GKE agnostic manifests via Helm)
—
Horizontal scaling of API pods, Celery workers, and LangGraph worker pool independently
CI/CD
GitHub Actions
—
Test → build → scan → staging → manual gate → prod
Observability
OpenTelemetry (traces/logs) + Prometheus (metrics) + Grafana (dashboards) + Sentry (error tracking)
—
Standard triad + error aggregation
IaC
Terraform
—
Reproducible cloud infra (VPC, RDS/managed Postgres, S3, Redis, EKS)

Explicit build-vs-buy call-outs
pgvector vs. a dedicated vector DB (Pinecone/Weaviate/Qdrant): at MVP-to-mid scale (tens of thousands of regulatory chunks per tenant corpus, low-single-digit millions org-wide), pgvector on well-tuned Postgres (HNSW index, appropriate work_mem) meets latency targets in §16 without adding a second stateful system to operate, back up, and keep consistent with the relational data. Trigger to reconsider: if total embedded chunks exceed ~10M or p95 vector search latency regresses past 300ms under load, re-evaluate a dedicated vector store behind the same RetrievalProvider interface (§5.4) — the abstraction is designed so this is a swap, not a rewrite.
Celery vs. Temporal/Airflow for background jobs: Celery is sufficient for recurrence/escalation/re-embedding sweeps, which are simple retryable jobs, not long-running stateful workflows — that role belongs to LangGraph + its Postgres checkpointer, not the task queue.

3. Repository Structure (Monorepo)
Single monorepo, managed with uv/poetry workspaces (Python) and pnpm workspaces (TS), orchestrated by Makefile + docker-compose.yml for local dev.
sera/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI app factory, middleware registration
│   │   ├── core/
│   │   │   ├── config.py               # Pydantic Settings, env loading
│   │   │   ├── security.py             # JWT issuance/verification, password hashing
│   │   │   ├── rbac.py                 # role/permission decorators
│   │   │   ├── db.py                   # async engine/session factory
│   │   │   ├── events.py               # domain event publisher interface
│   │   │   └── errors.py               # standard error response models
│   │   ├── modules/
│   │   │   ├── documents/              # Document Service
│   │   │   │   ├── router.py
│   │   │   │   ├── service.py
│   │   │   │   ├── repository.py
│   │   │   │   └── schemas.py
│   │   │   ├── knowledge/              # Regulatory KB + Org KB, embeddings, retrieval
│   │   │   │   ├── regulatory/
│   │   │   │   ├── organizational/
│   │   │   │   └── retrieval_provider.py
│   │   │   ├── workflow/               # Shared Workflow Document service — the core module
│   │   │   │   ├── router.py
│   │   │   │   ├── service.py          # read/write projection logic, write-lock rules (11.6)
│   │   │   │   ├── repository.py
│   │   │   │   └── schemas.py
│   │   │   ├── obligations/
│   │   │   ├── tasks/
│   │   │   ├── evidence/
│   │   │   ├── notifications/
│   │   │   ├── compliance/             # verification engine, scoring
│   │   │   ├── audit/
│   │   │   └── auth/
│   │   ├── ai/
│   │   │   ├── graph/
│   │   │   │   ├── build_graph.py      # LangGraph graph assembly
│   │   │   │   ├── nodes/              # one file per agent (Section 12 of PRD)
│   │   │   │   │   ├── applicability_agent.py
│   │   │   │   │   ├── obligation_extraction_agent.py
│   │   │   │   │   ├── change_analysis_agent.py
│   │   │   │   │   ├── ambiguity_detection_agent.py
│   │   │   │   │   ├── impact_mapping_agent.py
│   │   │   │   │   └── planning_agent.py
│   │   │   │   ├── checkpointer.py     # Postgres-backed LangGraph checkpointer wiring
│   │   │   │   └── projections.py      # SWD -> per-agent minimal context builder
│   │   │   ├── prompts/                # versioned prompt templates, one dir per agent
│   │   │   └── providers/              # LLMProvider, EmbeddingProvider abstractions
│   │   └── workers/
│   │       ├── celery_app.py
│   │       ├── scheduled/              # recurrence, escalation sweep, re-embedding
│   │       └── tasks.py
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── contract/                   # OpenAPI schema contract tests
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/
│   ├── app/                            # Next.js App Router
│   │   ├── (dashboard)/
│   │   ├── (regulatory-workspace)/
│   │   ├── (obligations)/
│   │   ├── (implementation)/
│   │   ├── (evidence)/
│   │   ├── (audit)/
│   │   ├── (settings)/
│   │   └── layout.tsx
│   ├── components/
│   │   ├── ui/                         # shadcn primitives
│   │   ├── workflow-inspector/         # SWD viewer component (PRD §35)
│   │   └── shared/
│   ├── lib/
│   │   ├── api-client/                 # generated from backend OpenAPI spec — DO NOT hand-edit
│   │   ├── auth/
│   │   └── hooks/
│   ├── package.json
│   └── Dockerfile
│
├── infra/
│   ├── terraform/
│   │   ├── modules/{vpc,rds,s3,redis,eks}/
│   │   └── envs/{dev,staging,prod}/
│   ├── helm/
│   │   ├── backend/
│   │   ├── frontend/
│   │   └── workers/
│   └── docker-compose.yml              # local dev: postgres+pgvector, redis, minio, backend, frontend
│
├── shared/
│   └── openapi/
│       └── sera-v1.yaml                # generated & committed — the frontend/backend contract of record
│
├── .github/workflows/
│   ├── ci.yml
│   ├── deploy-staging.yml
│   └── deploy-prod.yml
│
├── Makefile
└── README.md

Rule: the modules/* boundary in backend/app/modules/ mirrors the Service Map in the PRD (§25) exactly — one module per service. Cross-module imports are only allowed via each module's service.py public functions, never via another module's repository.py. This keeps the monorepo "modular monolith" honest and makes a future service extraction (e.g., pulling workflow out into its own deployable) a low-risk move.

4. Database Architecture
4.1 Principles
Single Postgres 16 instance (managed: RDS/Cloud SQL), one logical database, tenant isolation via organization_id + RLS — not separate databases/schemas per tenant (avoids migration fan-out at scale; revisit only if a specific enterprise tenant contractually requires physical isolation).
All tables have created_at, updated_at (trigger-maintained), and where relevant deleted_at (soft delete).
Every table that is tenant-scoped has a NOT NULL organization_id and an RLS policy (§4.4).
4.2 Full Schema (DDL-level)
-- ============ Tenancy & Identity ============
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    intermediary_type TEXT NOT NULL,   -- 'stock_broker' | 'depository_participant' | ...
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    email CITEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin','compliance_officer','department_head','operations','auditor','executive')),
    password_hash TEXT,                 -- null if SSO-only
    department_id UUID,                 -- FK added after org_departments exists
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============ Regulatory Knowledge Base (global, not tenant-scoped) ============
CREATE TABLE regulatory_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    circular_number TEXT,
    issue_date DATE,
    category TEXT,                      -- e.g. 'kyc', 'reporting', 'stock_broker'
    file_ref TEXT NOT NULL,              -- object storage key
    embedding_status TEXT NOT NULL DEFAULT 'pending', -- pending|processing|done|failed
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE regulatory_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES regulatory_documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(3072) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb   -- {clause, page, effective_date}
);
CREATE INDEX regulatory_chunks_embedding_hnsw
    ON regulatory_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX regulatory_chunks_metadata_gin ON regulatory_chunks USING GIN (metadata);

-- ============ Organizational Knowledge Base (tenant-scoped) ============
CREATE TABLE org_departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    name TEXT NOT NULL,
    head_user_id UUID REFERENCES users(id)
);

ALTER TABLE users ADD CONSTRAINT fk_users_department
    FOREIGN KEY (department_id) REFERENCES org_departments(id);

CREATE TABLE org_sops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    department_id UUID REFERENCES org_departments(id),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE org_sop_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sop_id UUID NOT NULL REFERENCES org_sops(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL,          -- denormalized for RLS performance
    chunk_text TEXT NOT NULL,
    embedding VECTOR(3072) NOT NULL
);
CREATE INDEX org_sop_chunks_embedding_hnsw
    ON org_sop_chunks USING hnsw (embedding vector_cosine_ops);

CREATE TABLE org_systems (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    name TEXT NOT NULL,
    owner_department_id UUID REFERENCES org_departments(id)
);

-- ============ Workflow (the Shared Workflow Document lives here) ============
CREATE TABLE workflow_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES regulatory_documents(id),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    status TEXT NOT NULL DEFAULT 'created',
        -- created|in_analysis|pending_approval_1|impact_mapping|planning|
        -- pending_approval_2|executing|monitoring|archived
    current_stage TEXT NOT NULL DEFAULT 'document_ingestion',
    swd JSONB NOT NULL DEFAULT '{}'::jsonb,   -- full Shared Workflow Document, PRD §11.4
    schema_version SMALLINT NOT NULL DEFAULT 1,  -- SWD schema version, for forward migrations
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX workflow_documents_swd_gin ON workflow_documents USING GIN (swd);
CREATE INDEX workflow_documents_org_status ON workflow_documents (organization_id, status);

-- LangGraph checkpoints (managed by langgraph-checkpoint-postgres, listed for completeness)
-- CREATE TABLE langgraph_checkpoints ( ... );  -- library-owned schema, migrated separately

-- ============ Obligations (materialized view of swd.agent_outputs, for querying) ============
CREATE TABLE obligations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflow_documents(id),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    description TEXT NOT NULL,
    owner_department_id UUID REFERENCES org_departments(id),
    frequency TEXT,                      -- 'one_time'|'annual'|'quarterly'|'monthly'
    evidence_type TEXT,
    status TEXT NOT NULL DEFAULT 'proposed',
        -- proposed|approved|rejected|compliant|non_compliant
    confidence_score NUMERIC(4,3),
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX obligations_org_status ON obligations (organization_id, status);

-- ============ Execution ============
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflow_documents(id),
    obligation_id UUID NOT NULL REFERENCES obligations(id),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    title TEXT NOT NULL,
    description TEXT,
    owner_department_id UUID REFERENCES org_departments(id),
    assignee_user_id UUID REFERENCES users(id),
    due_date DATE,
    status TEXT NOT NULL DEFAULT 'open',
        -- open|in_progress|submitted|verified|overdue
    evidence_requirement TEXT,
    priority TEXT NOT NULL DEFAULT 'medium',
    recurrence_rule TEXT,                -- iCal RRULE string, null if one-off
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX tasks_org_status_due ON tasks (organization_id, status, due_date);
CREATE INDEX tasks_assignee ON tasks (assignee_user_id);

CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    file_ref TEXT NOT NULL,
    uploaded_by UUID NOT NULL REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'pending',   -- pending|accepted|rejected
    validation_notes TEXT,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    validated_at TIMESTAMPTZ
);

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID NOT NULL REFERENCES users(id),
    type TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    channel TEXT NOT NULL,                -- 'email'|'slack'|'in_app'
    read BOOLEAN NOT NULL DEFAULT false,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============ Audit (append-only, no UPDATE/DELETE grants for app role) ============
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    workflow_id UUID REFERENCES workflow_documents(id),
    actor_type TEXT NOT NULL,             -- 'agent'|'user'|'system'
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    before JSONB,
    after JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX audit_log_org_created ON audit_log (organization_id, created_at DESC);
CREATE INDEX audit_log_workflow ON audit_log (workflow_id);

REVOKE UPDATE, DELETE ON audit_log FROM app_role;
GRANT INSERT, SELECT ON audit_log TO app_role;

4.3 Migration Strategy
Alembic, one migration per PR — never hand-edit a schema in prod.
SWD schema changes are handled via schema_version on workflow_documents, not Alembic — a background migrator upgrades old JSONB payloads lazily on read (write-through), so in-flight workflows aren't broken by a schema bump.
Destructive migrations (drop column/table) require a two-step process: deprecate in PR N, drop in PR N+2 minimum, across at least one full release cycle.
4.4 Row-Level Security
ALTER TABLE workflow_documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON workflow_documents
    USING (organization_id = current_setting('app.current_org_id')::uuid);
-- Repeat for: obligations, tasks, evidence, notifications, audit_log,
-- org_departments, org_sops, org_sop_chunks, org_systems, users.

app.current_org_id is set per-request by a FastAPI dependency immediately after JWT verification, inside the same transaction that runs the query — never trusted from client input.
4.5 Retention
audit_log and archived workflow_documents: retained indefinitely by default (regulatory record-keeping); configurable per-org retention policy is an open item (PRD §47).
evidence files: retained per org policy, minimum matching SEBI's own record-retention requirements for the underlying obligation category.

5. Vector Database & Retrieval Architecture
5.1 Two Corpora, Two Access Patterns
Corpus
Table
Scope
Refresh cadence
Regulatory KB
regulatory_chunks
Global (shared across tenants)
On new circular ingestion
Organizational KB
org_sop_chunks
Tenant-scoped
On SOP create/update

5.2 Chunking
Regulatory documents: chunked by clause/section boundary first (structural chunking using the PDF's own numbering, e.g., "4.2", "Annex B"), falling back to ~500-token sliding window with 15% overlap only where structure detection fails. Clause-boundary chunking is deliberate: it's what makes citations in agent output (Regulatory RAG results) map back to a specific, human-checkable clause instead of an arbitrary text window.
SOPs: paragraph-level chunking, ~300–500 tokens, 10% overlap.
5.3 Indexing
hnsw index (not ivfflat) on both chunk tables — better recall at the query volumes expected, acceptable build time given chunk counts are in the tens-of-thousands-per-tenant range, not billions.
metadata JSONB (clause, page, effective_date, category) is GIN-indexed to support hybrid search: vector similarity pre-filtered/post-filtered by metadata (e.g., "only chunks from 	circulars effective after 2023-01-01").
5.4 Retrieval Abstraction
class RetrievalProvider(Protocol):
    async def search_regulatory(
        self, query: str, filters: RegulatoryFilters, top_k: int = 8
    ) -> list[RetrievedChunk]: ...

    async def search_organizational(
        self, query: str, organization_id: UUID, top_k: int = 8
    ) -> list[RetrievedChunk]: ...

Every agent in §8 calls this interface, never regulatory_chunks/org_sop_chunks directly. This is the seam that lets pgvector be swapped for a dedicated vector store later (§2) without touching agent code.
5.5 Embedding Pipeline
Document Uploaded event → Celery task: extract text → structural chunk → batch-embed (batches of ≤100 chunks per API call to the embedding provider, to control latency and cost) → bulk INSERT into regulatory_chunks/org_sop_chunks → set embedding_status = 'done' → emit Document Embedded event, which unblocks any workflow waiting on that document.
5.6 Consistency Guarantee
Because embeddings live in the same Postgres transaction boundary as the rest of the data, a chunk and its parent document row are never in an inconsistent state that a separate vector DB + relational DB pairing would otherwise need to reconcile (e.g., no "vector exists but parent row was rolled back" class of bugs).

6. API Architecture
6.1 Conventions
Base path: /api/v1. Breaking changes require /api/v2; v1 stays live for a documented deprecation window.
All responses: application/json, snake_case keys.
Pagination: cursor-based (?cursor=...&limit=...), never offset-based, for all list endpoints — offset pagination degrades badly on tasks/audit_log at scale and is unsafe under concurrent writes.
Standard error envelope:
{ "error": { "code": "OBLIGATION_NOT_APPROVED", "message": "...", "request_id": "..." } }

Idempotency: mutating POSTs that create a resource accept an Idempotency-Key header; server stores (key, org_id) -> response for 24h and replays on retry instead of double-creating.
Every endpoint requires a valid JWT except /auth/* and /healthz.
OpenAPI spec (shared/openapi/sera-v1.yaml) is generated from FastAPI at build time and committed — it is the contract of record; the frontend API client is generated from this file, not hand-written, so contract drift fails CI rather than shipping.
6.2 Endpoint Catalogue
Auth
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
GET    /api/v1/auth/me

Documents
POST   /api/v1/documents                       -> 201 {document_id, embedding_status}
GET    /api/v1/documents/{id}
GET    /api/v1/documents?cursor=&category=&status=

Workflows (Shared Workflow Document)
POST   /api/v1/workflows                       # usually system-triggered on Document Embedded
GET    /api/v1/workflows/{id}                  # full SWD (RBAC: compliance_officer/admin/auditor)
GET    /api/v1/workflows/{id}/notes            # agent_notes projection
GET    /api/v1/workflows/{id}/tasks            # agent_tasks projection
PATCH  /api/v1/workflows/{id}                  # advance stage (system-internal, service-to-service auth only)
POST   /api/v1/workflows/{id}/notes            # human-authored note
POST   /api/v1/workflows/{id}/agent-tasks/{task_id}/resolve
GET    /api/v1/workflows?cursor=&status=&organization_id=

Obligations
GET    /api/v1/obligations?cursor=&status=&department_id=
GET    /api/v1/obligations/{id}
PATCH  /api/v1/obligations/{id}                # {action: approve|edit|reject, edits?, comment?}

Tasks
GET    /api/v1/tasks?cursor=&status=&assignee_id=&overdue=true
POST   /api/v1/tasks
PATCH  /api/v1/tasks/{id}

Evidence
POST   /api/v1/evidence                        # multipart upload, requires task_id
GET    /api/v1/evidence/{id}
POST   /api/v1/evidence/{id}/validate           # {decision: accept|reject, notes}

Compliance
GET    /api/v1/dashboard
GET    /api/v1/compliance-score?department_id=&period=

Notifications
GET    /api/v1/notifications?cursor=&unread_only=true
PATCH  /api/v1/notifications/{id}/read

Audit
GET    /api/v1/audit?cursor=&workflow_id=&entity_type=
GET    /api/v1/audit/export?format=pdf|csv
GET    /api/v1/audit/{workflow_id}              # frozen SWD + full audit trail for one workflow

6.3 Request/Response Contract Example
PATCH /api/v1/obligations/{id}
Request:
  action: "edit"
  edits:
    description: "..."
    owner_department_id: "uuid"
    frequency: "annual"
  comment: "Reassigned to Ops per department head clarification."
Response 200:
  id: uuid
  status: "approved"
  description: "..."
  approved_by: uuid
  approved_at: timestamp
Response 409:
  error:
    code: "OBLIGATION_ALREADY_FINALIZED"


7. Backend Service Architecture
7.1 Layering (per module)
router.py       -> HTTP concerns only: parse request, call service, map response/errors
service.py      -> business logic, orchestrates repository + event publishing
repository.py   -> SQL/ORM queries, the ONLY place raw SQLAlchemy queries live
schemas.py      -> Pydantic request/response models

No router ever touches a repository directly; no service ever constructs raw SQL. This is enforced by a CI lint rule (import-linter) that fails a PR if router.py imports from repository.py.
7.2 Domain Events
Internal event contract (published to Redis Streams, consumed by workers and the notification service):
class DomainEvent(BaseModel):
    event_type: str              # "document.uploaded", "obligation.approved", ...
    organization_id: UUID
    workflow_id: UUID | None
    payload: dict
    occurred_at: datetime
    idempotency_key: str         # dedupes redelivery

Event catalogue matches PRD §15 exactly — this table is the single mapping between "thing that happened" and "who reacts":
Event
Publisher
Consumers
document.uploaded
Document Service
Embedding worker
document.embedded
Embedding worker
Workflow Service (creates SWD)
workflow.stage_completed
Workflow Service
LangGraph orchestrator (advance graph)
obligation.approved
Obligation Service
Workflow Service (unblocks Impact Mapping node)
implementation.approved
Workflow Service
Task Service (generate tasks)
task.created / task.overdue
Task Service
Notification Service
evidence.uploaded
Evidence Service
Compliance Verification Service
compliance.gap_detected
Verification Service
Notification Service (escalation)

7.3 Redis Streams vs. Kafka
Redis Streams chosen over Kafka for MVP/mid-scale: lower operational overhead, already required for Celery + caching, sufficient throughput for this event volume (human-paced compliance workflows, not high-frequency trading). Trigger to reconsider: multi-region deployment or >~5k events/sec sustained — re-evaluate Kafka/MSK behind the same EventPublisher/EventConsumer interface.

8. AI Orchestration Layer (LangGraph)
8.1 Graph Definition
One LangGraph StateGraph per workflow type (currently one type: standard circular processing). Nodes map 1:1 to PRD §12 agents plus two interrupt() nodes for human approval gates.
graph = StateGraph(WorkflowState)
graph.add_node("applicability", applicability_agent)
graph.add_node("obligation_extraction", obligation_extraction_agent)
graph.add_node("change_analysis", change_analysis_agent)
graph.add_node("ambiguity_detection", ambiguity_detection_agent)
graph.add_node("gate_1", human_gate_1)          # interrupt() until human_approvals written
graph.add_node("impact_mapping", impact_mapping_agent)
graph.add_node("planning", planning_agent)
graph.add_node("gate_2", human_gate_2)          # interrupt() until human_approvals written
graph.add_node("execution_handoff", handoff_to_execution_engine)  # deterministic, hands off to Task Service

8.2 Node Contract (every agent node implements this exactly)
async def agent_node(state: WorkflowState) -> WorkflowState:
    ctx = build_projection(state.workflow_id, fields=REQUIRED_FIELDS[agent_name])  # §8.3
    retrieved = await retrieval_provider.search_regulatory(...)   # if applicable
    result = await llm_provider.generate_structured(
        prompt=render_prompt(agent_name, ctx, retrieved),
        response_schema=AGENT_OUTPUT_SCHEMAS[agent_name],         # Pydantic model, enforced
    )
    await workflow_service.write_agent_output(state.workflow_id, agent_name, result)
    await workflow_service.append_execution_history(state.workflow_id, agent_name, "completed")
    await event_publisher.publish("workflow.stage_completed", {...})
    return state.advance()

8.3 Context Projection (the token-savings mechanism)
build_projection() returns only the SWD fields a given agent actually needs — e.g., the Impact Mapping agent receives agent_outputs.obligation_extraction_agent, document_metadata, and affected_departments (if partially filled), not the full execution_history or other agents' raw reasoning. REQUIRED_FIELDS is an explicit allowlist per agent, reviewed in code review whenever an agent's prompt changes — this is intentionally not "smart"/automatic, because an explicit allowlist is auditable and an inferred one isn't.
8.4 Checkpointing
langgraph-checkpoint-postgres backs the graph's checkpointer with the same Postgres instance. On any node failure (LLM timeout, validation failure), the graph resumes from the last successful checkpoint — mapped 1:1 to workflow_documents.current_stage — rather than restarting the whole pipeline. Checkpoints are pruned after workflow archival (raw checkpoint blobs, not the SWD itself, which is retained per §4.5).
8.5 Structured Output Enforcement
Every agent's LLM call specifies a Pydantic response_schema; the LLM provider wrapper validates the response and retries (max 2 attempts, then routes to a agent_task for human review) on schema-validation failure — this is what makes "AI output is data, not code" (§1.3) an enforced property, not a guideline.

9. Event Bus & Background Processing
Redis Streams — domain events (§7.2).
Celery — scheduled/retryable jobs:
recurrence_sweep (hourly): re-opens tasks for obligations whose recurrence is due.
escalation_sweep (hourly): finds overdue tasks, walks the escalation ladder, publishes task.overdue.
embedding_pipeline (event-triggered, not scheduled): document → chunks → embeddings.
compliance_score_recompute (nightly): recomputes and caches (Redis, 24h TTL) dashboard aggregates.
Celery tasks are idempotent by design (safe to re-run): each checks current DB state before acting rather than assuming it's the only invocation.

10. Frontend Architecture
Next.js App Router, route groups matching PRD §33 nav structure exactly ((dashboard), (obligations), etc.).
Server Components by default for read-heavy views (Dashboard, Audit Viewer); Client Components only where interactivity is required (Obligation approve/edit forms, Workflow Inspector's live-updating panel).
Data fetching: server components call the backend directly (server-to-server, short-lived service JWT); client components use the generated api-client (from shared/openapi/sera-v1.yaml) with React Query for cache/invalidation.
Real-time updates: workflow stage changes and notifications pushed via Server-Sent Events from a lightweight /api/v1/stream endpoint subscribed to the same Redis Streams as backend consumers — avoids polling on the Workflow Document Inspector view.
State management: React Query for server state; minimal local UI state via component state/useReducer — no global client store (Redux/Zustand) needed given how server-state-heavy this app is.

11. Authentication, Authorization & Multi-Tenancy
Auth: password + JWT (access 15 min / refresh 7 days) for direct signup tenants; OIDC/SAML SSO for enterprise tenants, mapped to the same internal users table and role model post-federation.
RBAC: enforced via a FastAPI dependency (require_role(...)) on every route; the same role table drives both API authorization and frontend control visibility (frontend hides, backend actually enforces — §1 principle 5).
Multi-tenancy: organization_id on every tenant-scoped table + RLS (§4.4). The JWT carries organization_id; a FastAPI dependency sets app.current_org_id inside the request's DB transaction before any query runs.
Service-to-service auth (e.g., LangGraph workers calling the Workflow Service): short-lived signed service tokens, distinct from user JWTs, scoped to specific internal routes only (PATCH /workflows/{id} for stage advancement is not reachable by user JWTs at all).

12. Infrastructure & Deployment
12.1 Environments
dev (local Docker Compose) → staging (full k8s, synthetic data) → prod (full k8s, real tenants). Terraform workspaces per environment under infra/terraform/envs/.
12.2 Kubernetes Layout
Deployments: backend-api (FastAPI, HPA on CPU + request latency), celery-worker (HPA on queue depth), langgraph-worker (separate pool from celery — LLM-call-bound, scaled on in-flight-workflow count, not CPU), frontend.
StatefulSets/managed services: Postgres (RDS/Cloud SQL, not self-hosted in k8s), Redis (managed, e.g. ElastiCache).
Ingress: single ALB/Ingress with path-based routing to frontend and /api → backend-api.
Secrets: k8s Secrets sourced from a managed secrets manager (AWS Secrets Manager/GCP Secret Manager) via an operator — never committed, never baked into images.
12.3 CI/CD
PR opened → lint + unit tests + contract tests (OpenAPI diff check) → build images
→ push to registry → deploy to staging → smoke tests → manual approval gate → deploy to prod

OpenAPI diff check specifically fails the PR if a backend change alters shared/openapi/sera-v1.yaml without the frontend api-client being regenerated in the same PR — this is the enforcement mechanism for §6.1's contract-of-record rule.

13. Security & Compliance Requirements
Encryption: TLS 1.2+ everywhere; AES-256 at rest for S3/MinIO (SSE) and for Postgres (managed disk encryption + column-level encryption for any PII fields beyond what RLS+TLS already protects).
Secrets: no secret ever in env files committed to git; local dev uses .env.local (gitignored) with dummy values, real secrets only via the secrets manager.
Password hashing: Argon2id.
Signed URLs: all evidence/document downloads via short-TTL (5–15 min) pre-signed S3 URLs, never public buckets.
Audit immutability: audit_log has no UPDATE/DELETE grant for the application DB role (§4.2) — even a compromised app cannot rewrite history; only a break-glass DBA role (separately audited) could, and that action itself would be logged by Postgres-level audit extensions (e.g., pgAudit).
Dependency scanning: pip-audit/npm audit + Dependabot in CI; container image scanning (Trivy) before any deploy.
Least privilege: the app's DB role has no DROP/CREATE TABLE privileges in prod — schema changes only via the migration pipeline's dedicated migrator role.
PII handling: any personally identifiable data in evidence/SOPs is treated as sensitive by default; access to evidence files is itself an audited action (already required by PRD §30).

14. Testing Strategy
Layer
Tooling
Coverage bar
Unit
pytest (backend), vitest (frontend)
Every service.py function; every LangGraph node's output-schema validation path
Integration
pytest against a real Postgres (Testcontainers)
Every module's repository + RLS policy (explicit cross-tenant leak test per table)
Contract
Schemathesis against sera-v1.yaml
Every endpoint fuzz-tested against its declared schema
E2E
Playwright
The five user stories in PRD §7, end to end through the UI
AI-specific
Golden-set regression suite
Fixed set of real (anonymized) circulars with human-labeled expected obligations; run on every prompt/model change, diffed against baseline extraction accuracy (PRD target: >80%)
Load
k6
Validates §16 SLA targets under simulated concurrent-tenant load

Non-negotiable: any PR touching RLS policies must include a test that asserts a user from Org A cannot read/write Org B's row for that table.

15. Observability & SRE
Tracing: OpenTelemetry spans across API → service → repository → (if applicable) LangGraph node → LLM call, so a single slow request is traceable end-to-end including which agent/prompt was the bottleneck.
Metrics (Prometheus): per PRD §40 — API latency, agent execution time, queue depth, task completion rate, notification delivery rate, evidence validation time, LLM token usage, confidence-score distribution, human-override rate.
Dashboards (Grafana): one dashboard per service map entry (§7's table), plus one "workflow health" dashboard showing in-flight workflows by current_stage.
Error tracking: Sentry for both backend and frontend, correlated by request_id.
Alerting: PagerDuty/Opsgenie integration on: LLM provider failure rate > threshold, DB connection pool exhaustion, p95 API latency breach, checkpoint-resume failures (a stuck workflow is a compliance risk, not just a bug).

16. Non-Functional Requirements / SLAs
Metric
Target
API p95 latency
< 300 ms (excluding AI-pipeline endpoints)
Dashboard load
< 2 s
Document upload
< 5–10 s
Full AI agent pipeline (upload → Gate 1 ready)
< 60 s
Impact mapping
< 30 s
Vector search (either corpus)
< 500 ms p95
Availability (API)
99.9% monthly
RPO
15 minutes
RTO
2 hours


17. Environment & Configuration Reference
Minimum required environment variables (backend):
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
S3_ENDPOINT / S3_BUCKET / S3_ACCESS_KEY / S3_SECRET_KEY
JWT_SECRET / JWT_REFRESH_SECRET
ANTHROPIC_API_KEY / OPENAI_API_KEY
EMBEDDING_MODEL=text-embedding-3-large
LANGGRAPH_CHECKPOINT_DSN=postgresql://...   # can equal DATABASE_URL
OIDC_ISSUER_URL / OIDC_CLIENT_ID / OIDC_CLIENT_SECRET   # enterprise SSO, optional per tenant
SENTRY_DSN
OTEL_EXPORTER_OTLP_ENDPOINT


18. Appendix: Naming & Coding Conventions
Tables/columns: snake_case, plural table names, singular FK column names (owner_department_id, not department_ids).
API fields: snake_case in JSON (matches Pydantic defaults, avoids a translation layer).
Domain events: noun.verb_past_tense (obligation.approved, not approve_obligation).
Branch naming: feat/<module>-<short-desc>, fix/<module>-<short-desc> — matching the PR backlog in the Master PRD §45.
Commit convention: Conventional Commits (feat:, fix:, chore:), enforced via commitlint in CI.
Prompt versioning: every file under backend/app/ai/prompts/<agent>/ is versioned (v1.py, v2.py); the graph always references a pinned version, and prompt changes are a reviewed PR with the golden-set regression suite (§14) run and attached.
