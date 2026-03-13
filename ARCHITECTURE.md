# Architecture & Technical Design

This document provides detailed technical information about AeroInsight's architecture, RAG pipeline, and design decisions.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                  React Frontend (Port 3000)                     │
│          Vite Dev Server + Tailwind CSS + Framer Motion        │
└─────────────────┬───────────────────────────────────────────────┘
                  │ HTTP/REST
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                        │
│   Concept CRUD + Evaluation + Report CRUD/Upload Endpoints      │
│                       Port 8001                                 │
└──────┬──────────────────────────────────────────┬───────────────┘
       │                                          │
       │ SQLAlchemy ORM                           │ RAG Service
       ▼                                          ▼
┌──────────────────┐                    ┌────────────────────────┐
│  SQLite Database │                    │   RAG Pipeline         │
│  - Concepts      │                    │  1. Text Embedding     │
│  - Evaluations   │                    │  2. Vector Retrieval   │
│  - Reports       │                    │  3. LLM Evaluation     │
└──────────────────┘                    └───┬──────────────┬─────┘
                                            │              │
                                            ▼              ▼
                                   ┌─────────────┐  ┌─────────────┐
                                   │  ChromaDB   │  │ OpenAI GPT-4│
                                   │ 31,652 chunks│  │ Structured  │
                                   └─────────────┘  │ JSON Output │
                                                    └─────────────┘
```

---

## Report Ingestion & Vector CRUD

Reports are first-class resources with dedicated API endpoints (`/api/v1/reports`) and a synchronized vector index lifecycle.

### Upload / Create Flow

1. Frontend uploads PDF via multipart form data.
2. `report_service.extract_pdf_text()` parses text using `pypdf`.
3. Text is persisted in SQLite `reports` table.
4. Text is chunked (`512` chars, `64` overlap).
5. Chunks are embedded with `all-MiniLM-L6-v2`.
6. Chunks are upserted into ChromaDB with deterministic ids:

```text
report_{report_id}::chunk::{chunk_index}
```

### Update Flow

- Metadata-only updates persist directly in SQLite.
- Content/title updates trigger re-index:
1. Delete old vectors by metadata filter `{"report_id": <id>}`.
2. Re-chunk and re-embed updated content.
3. Upsert new vectors.

### Delete Flow

1. Delete vectors from ChromaDB by `report_id`.
2. Delete report row from SQLite.

This ordering prevents stale vectors after report deletion.

---

## RAG Pipeline Deep Dive

### Step-by-Step Evaluation Flow

#### 1. Text Embedding

```python
# app/services/rag_service.py
def _embed_text(self, text: str) -> np.ndarray:
    return self.embedding_model.encode(text, convert_to_numpy=True)
```

- **Model**: `all-MiniLM-L6-v2` (SentenceTransformers)
- **Dimensions**: 384
- **Speed**: ~50ms per embedding (CPU)
- **Why Local?** Free, fast, privacy-preserving

#### 2. Semantic Retrieval

```python
results = self.collection.query(
    query_embeddings=[embedding.tolist()],
    n_results=5,
    include=["documents", "metadatas", "distances"]
)
```

- **Database**: ChromaDB with persistent storage
- **Search Type**: Cosine similarity
- **Results**: Top 5 most relevant chunks
- **Metadata**: arXiv ID, title, authors, publish date

#### 3. Prompt Construction

```python
system_prompt = """You are an expert aerodynamics researcher evaluating novel concepts.
Return structured JSON with novelty_score, confidence_score, mechanisms, tradeoffs, regulatory."""

user_prompt = f"""
Concept: {title}
Description: {description}

Retrieved Research:
{chunk_1_with_citation}
{chunk_2_with_citation}
...

Evaluate this concept based on the research.
"""
```

#### 4. LLM Evaluation

```python
response = self.openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    response_format={"type": "json_object"}
)
```

- **Model**: GPT-4o (upgraded from GPT-4o-mini for better reasoning)
- **Response Format**: Structured JSON enforced via API
- **Output**: Novelty score, confidence, mechanisms, tradeoffs, regulatory flags

#### 5. Persistence

```python
evaluation = ConceptEvaluation(
    concept_id=concept.id,
    novelty_score=float(data["novelty_score"]),
    confidence_score=float(data["confidence_score"]),
    mechanisms=data.get("mechanisms", []),
    tradeoffs=data.get("tradeoffs", {}),
    regulatory=data.get("regulatory", []),
    summary=data.get("summary")
)
db.add(evaluation)
db.commit()
```

### Performance Metrics

| Operation | Duration |
|-----------|----------|
| Text Embedding | ~50ms |
| Vector Retrieval | ~200ms |
| LLM Evaluation | ~2-4s |
| Database Save | ~50ms |
| **Total** | **~3-5s** |

---

## Database Schema

### Entity-Relationship Diagram

```
┌─────────────────────────────┐
│       AeroConcept           │
├─────────────────────────────┤
│ id (PK)                     │
│ title                       │
│ description                 │
│ author                      │
│ tags (JSON)                 │
│ status                      │
│ created_at                  │
│ updated_at                  │
└──────────┬──────────────────┘
           │ 1:1
           │ ON DELETE CASCADE
           ▼
┌─────────────────────────────┐
│   ConceptEvaluation         │
├─────────────────────────────┤
│ id (PK)                     │
│ concept_id (FK, UNIQUE)     │
│ novelty_score               │
│ confidence_score            │
│ mechanisms (JSON)           │
│ tradeoffs (JSON)            │
│ regulatory (JSON)           │
│ summary                     │
│ created_at                  │
└─────────────────────────────┘

┌─────────────────────────────┐
│           Report            │
├─────────────────────────────┤
│ id (PK)                     │
│ title                       │
│ source_filename             │
│ content                     │
│ author                      │
│ tags (JSON)                 │
│ chunk_count                 │
│ created_at                  │
│ updated_at                  │
└─────────────────────────────┘
```

### Key Constraints

- **One-to-One**: Each concept has at most one evaluation
- **Cascade Delete**: Deleting concept removes its evaluation
- **Report-Vector Sync**: Report delete/update operations also delete/reindex vectors by `report_id`
- **JSON Storage**: Arrays/objects stored as JSON strings (SQLite limitation)
- **Status Enum**: `SUBMITTED` or `ANALYSED`

---

## Frontend Design System

### Cockpit Theme Philosophy

Inspired by fighter jet cockpits (Saab 9000s design principles):
- **Functional First**: Every element serves a purpose
- **High Contrast**: Critical information stands out
- **Consistent Patterns**: Reduce cognitive load
- **Efficient Workflow**: Minimal clicks

### Color Palette

```css
--cockpit-bg: #0a0e14;          /* Deep space background */
--cockpit-primary: #ff9500;     /* Amber HUD indicators */
--cockpit-secondary: #00d9ff;   /* Cyan displays */
--cockpit-danger: #ff4757;      /* Red alerts */
--cockpit-success: #2ecc71;     /* Green status */
--cockpit-text: #e5e7eb;        /* Light gray text */
--cockpit-muted: #6b7280;       /* Muted secondary text */
```

### Typography

- **Headers**: Rajdhani (geometric, technical)
- **Body**: System sans-serif stack
- **Code/Metrics**: JetBrains Mono

### Component Patterns

**Panels**:
```jsx
<div className="panel">
  <h2 className="panel-title">Mission Control</h2>
  {/* Content */}
</div>
```

**Buttons**:
```jsx
<button className="btn-primary">Evaluate</button>    {/* Amber */}
<button className="btn-secondary">Edit</button>      {/* Cyan */}
<button className="btn-danger">Delete</button>       {/* Red */}
```

**Badges**:
```jsx
<span className="badge badge-cyan">SUBMITTED</span>
<span className="badge badge-green">ANALYSED</span>
```

**Metrics**:
```jsx
<div className="metric">
  <div className="metric-value">0.85</div>
  <div className="metric-label">Novelty Score</div>
</div>
```

### Animation Guidelines

All animations use Framer Motion:
- **Entry**: 0.3s slide-in + fade-in
- **Stagger**: 0.1s delay between list items
- **Hover**: 0.2s scale + glow
- **Loading**: 1.5s pulse

```jsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.3 }}
>
  {children}
</motion.div>
```

---

## Key Design Decisions

### Why SentenceTransformers Over OpenAI Embeddings?

| Factor | SentenceTransformers | OpenAI |
|--------|---------------------|--------|
| Cost | Free (after download) | ~$0.0001/1K tokens |
| Speed | 50ms (no network) | 200-500ms (API latency) |
| Privacy | Data never leaves system | Sent to OpenAI |
| Consistency | Same model for ingest/query | Potential model updates |

**Decision**: SentenceTransformers for cost, speed, and privacy.

### Why ChromaDB Over Pinecone/Weaviate?

| Factor | ChromaDB | Pinecone/Weaviate |
|--------|----------|-------------------|
| Setup | Single line, local | External service, API keys |
| Cost | Free | Paid tiers required |
| Performance | Fast for 31K chunks | Better at millions of vectors |
| Development | Easy reset/modify | More complex state management |

**Decision**: ChromaDB for simplicity and local development.

### Why GPT-4o Over GPT-4o-mini?

| Factor | GPT-4o | GPT-4o-mini |
|--------|--------|-------------|
| Reasoning | Superior logical analysis | Good but simpler |
| JSON Adherence | More reliable structured output | Occasional format issues |
| Context Handling | No degradation with long context | Some degradation |
| Cost | ~10x more expensive | Cheaper |
| Quality | Significantly better evaluations | Adequate for simple cases |

**Decision**: GPT-4o for evaluation quality despite higher cost.

### Why SQLite Over PostgreSQL?

For development and small deployments:
- **Simplicity**: No separate database server
- **Portability**: Single file database
- **Performance**: Fast enough for single-user workloads
- **Future**: Easy migration to PostgreSQL if needed

**Production Recommendation**: Use PostgreSQL for multi-user deployments.

---

## Project Structure

```
aerodynamic_RAG__analyser/
├── app/                          # Backend FastAPI application
│   ├── api/                      # API route handlers
│   │   ├── concepts.py           # Concept CRUD endpoints
│   │   ├── evaluations.py        # Evaluation endpoints
│   │   └── reports.py            # Report upload/CRUD endpoints
│   ├── core/                     # Core configurations
│   │   ├── config.py             # Environment variables
│   │   ├── database.py           # SQLAlchemy setup
│   │   └── exceptions.py         # Custom exceptions
│   ├── domain/                   # Domain models
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   └── schemas.py            # Pydantic schemas
│   ├── services/                 # Business logic
│   │   ├── rag_service.py        # RAG pipeline
│   │   └── report_service.py     # PDF extraction + report indexing
│   └── main.py                   # FastAPI app + exception handlers
│
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── layout/           # Layout (Sidebar, Layout)
│   │   │   ├── concepts/         # Concept components
│   │   │   ├── evaluations/      # Evaluation displays
│   │   │   ├── reports/          # Report CRUD components
│   │   │   └── common/           # Reusable (Toast, ErrorBoundary)
│   │   ├── pages/                # Page components
│   │   ├── services/             # API layer
│   │   │   └── api.js            # HTTP requests
│   │   ├── utils/                # Utilities
│   │   │   └── errors.js         # Error handling
│   │   └── App.jsx               # Router setup
│   ├── vite.config.js            # Vite configuration
│   └── tailwind.config.js        # Tailwind theme
│
├── scripts/                      # Utility scripts
│   ├── fetch_papers.py           # Fetch arXiv papers
│   ├── ingest_documents.py       # Initial data ingestion
│   ├── verify_retrieval.py       # Test retrieval quality
│   └── demo_mcp_flow.py          # MCP workflow demo
│
├── tests/                        # Test suites
│   ├── test_api_errors.py        # API error tests (16)
│   ├── test_concepts.py          # CRUD tests (13)
│   ├── test_database_errors.py   # DB transaction tests (13)
│   ├── test_e2e.py               # End-to-end tests (8)
│   └── test_reports.py           # Report endpoint tests (5)
│
├── chroma_storage/               # ChromaDB persistence
├── .env                          # Environment variables
├── requirements.txt              # Python dependencies
├── README.md                     # Quick start guide
├── TESTING.md                    # Testing documentation
└── ARCHITECTURE.md               # This file
```

---

## API Endpoints

### Concepts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/concepts` | List concepts (filterable, paginated) |
| GET | `/api/v1/concepts/{id}` | Get single concept |
| POST | `/api/v1/concepts` | Create new concept |
| PUT | `/api/v1/concepts/{id}` | Update concept |
| DELETE | `/api/v1/concepts/{id}` | Delete concept (cascade) |

### Evaluations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/concepts/{id}/evaluate` | Evaluate concept (RAG pipeline) |
| GET | `/api/v1/concepts/{id}/evaluation` | Get cached evaluation |

### Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/reports` | Upload PDF report and index into ChromaDB |
| GET | `/api/v1/reports` | List reports (paginated) |
| GET | `/api/v1/reports/{id}` | Get report details and extracted text |
| PUT | `/api/v1/reports/{id}` | Update report metadata/content (reindex on content/title changes) |
| DELETE | `/api/v1/reports/{id}` | Delete report and indexed vectors |

### Health & Discovery

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check with system status |
| GET | `/api/v1/mcp` | MCP tool discovery |

---

## Request/Response Examples

### Create Concept

**Request**:
```json
POST /api/v1/concepts
{
  "title": "Morphing Wing with Active Flow Control",
  "description": "A wing design that dynamically changes camber using boundary layer suction to optimize aerodynamic performance across flight regimes",
  "author": "Dr. Jane Smith",
  "tags": ["morphing", "active-control", "aerodynamics"]
}
```

**Response**: `201 Created`
```json
{
  "id": 1,
  "title": "Morphing Wing with Active Flow Control",
  "description": "A wing design that dynamically changes camber...",
  "author": "Dr. Jane Smith",
  "tags": ["morphing", "active-control", "aerodynamics"],
  "status": "SUBMITTED",
  "created_at": "2026-03-08T10:30:00Z",
  "updated_at": "2026-03-08T10:30:00Z"
}
```

### Evaluate Concept

**Request**:
```json
POST /api/v1/concepts/1/evaluate
```

**Response**: `202 Accepted`
```json
{
  "id": 1,
  "concept_id": 1,
  "novelty_score": 0.82,
  "confidence_score": 0.91,
  "mechanisms": [
    "Boundary layer suction reduces separation",
    "Variable camber optimizes lift distribution"
  ],
  "tradeoffs": {
    "complexity": "Increased mechanical complexity vs performance gain",
    "weight": "Actuator weight vs drag reduction benefit"
  },
  "regulatory": [
    "FAA certification may require additional testing",
    "Active control systems need redundancy for safety"
  ],
  "summary": "Moderately novel concept combining established principles...",
  "retrieved_context": [
    {
      "arxiv_id": "2301.12345",
      "title": "Active Flow Control for High-Lift Systems",
      "authors": ["J. Doe", "M. Smith"],
      "similarity": 0.89,
      "excerpt": "Boundary layer suction has been shown to..."
    }
  ],
  "created_at": "2026-03-08T10:31:15Z"
}
```

---

## Performance Optimization

### Backend Optimizations

1. **Caching**: Evaluations cached in SQLite (avoid re-evaluation)
2. **Connection Pooling**: SQLAlchemy manages DB connections
3. **Async Potential**: FastAPI supports async endpoints (future enhancement)
4. **Batch Embeddings**: Could batch multiple concepts for efficiency

### Frontend Optimizations

1. **Code Splitting**: Routes lazy-loaded with React.lazy()
2. **Memoization**: Use React.memo() for expensive components
3. **Virtual Scrolling**: For large concept lists (future enhancement)
4. **API Caching**: SWR or React Query (future enhancement)

### Database Optimizations

1. **Indexes**: Add indexes on frequently queried fields
```sql
CREATE INDEX idx_concepts_status ON concepts(status);
CREATE INDEX idx_concepts_created ON concepts(created_at DESC);
```

2. **Query Optimization**: Use select_related to avoid N+1 queries

### Vector Store Optimizations

1. **Collection Size**: Currently 31,652 chunks is well within ChromaDB's sweet spot
2. **Distance Metric**: Cosine similarity is efficient for normalized embeddings
3. **Result Limiting**: Top-5 retrieval keeps latency low

---

## Security Considerations

### API Security

- Environment variable validation on startup
- Input validation via Pydantic schemas
- SQL injection protection via SQLAlchemy ORM
- CORS configuration for frontend domain

### Deployment Recommendations

1. **HTTPS**: Use TLS certificates in production
2. **API Keys**: Rotate OpenAI keys regularly
3. **Rate Limiting**: Add rate limiting middleware
4. **Authentication**: Add JWT authentication for multi-user
5. **Input Sanitization**: Already handled by Pydantic

---

## Scalability Considerations

### Current Limits

| Resource | Limit | Notes |
|----------|-------|-------|
| Papers in ChromaDB | 31,652 chunks | ~350 papers |
| Concepts in SQLite | ~100K | Single-file database |
| Concurrent Users | ~10 | Single process FastAPI |
| API Rate Limit | OpenAI tier limit | Account dependent |

### Scale-Up Path

1. **Database**: Migrate to PostgreSQL with connection pooling
2. **Vector Store**: Migrate to Pinecone/Weaviate for millions of vectors
3. **API**: Deploy multiple instances behind load balancer
4. **Caching**: Add Redis for session/query caching
5. **CDN**: Serve frontend from CDN (Cloudflare, Vercel)

---

*Last Updated: March 2026*
