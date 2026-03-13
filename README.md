# AeroInsight RAG Analyser

AI-powered evaluation of aerodynamic concepts using Retrieval-Augmented Generation (RAG) with arXiv research papers.

## What It Does

Submit aerodynamic concepts → Get AI evaluations backed by real research papers

1. **Vector Search**: Queries 31,652 chunks from 248 arXiv papers
2. **LLM Evaluation**: GPT-4o analyzes novelty, mechanisms, and tradeoffs
3. **Structured Output**: Novelty scores, confidence, regulatory flags, citations
4. **Report CRUD + Indexing**: Upload/manage PDF reports and keep vectors synced in ChromaDB

**Stack**: FastAPI + React + ChromaDB + OpenAI + SQLite

---

## Quick Start

### Prerequisites

- Python 3.12+ with `uv` package manager
- Node.js 20+
- OpenAI API Key ([get one](https://platform.openai.com/api-keys))

### Setup

```bash
# 1. Clone and setup Python environment
git clone <repository-url>
cd aerodynamic_RAG__analyser
uv sync
# Optional: drop into the project virtualenv shell
# uv shell

# 2. Configure environment
# Create .env file with:
OPENAI_API_KEY=sk-proj-your-key-here
DATABASE_URL=sqlite:///./database.db
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION_NAME=aero_literature

# 3. Initialize database
uv run python scripts/fetch_papers.py       # One-time: grabs papers from arxiv
uv run python scripts/ingest_documents.py  # One-time: ingests 248 papers (~10-15 min)

# 4. Start backend
uv run uvicorn app.main:app --reload --port 8001
# Running at http://localhost:8001

# 5. Start frontend (new terminal)
cd frontend
npm install
npm run dev
# Running at http://localhost:3000
```

**Verify**: Open http://localhost:3000 and create a concept.

Note: if you do not run `uv shell`, prefix Python commands with `uv run` so they always execute inside the uv-managed virtual environment.

---

## API Overview

### REST Endpoints

```bash
# Concepts
GET    /api/v1/concepts              # List concepts (paginated, filterable)
GET    /api/v1/concepts/{id}         # Get single concept
POST   /api/v1/concepts              # Create concept
PUT    /api/v1/concepts/{id}         # Update concept
DELETE /api/v1/concepts/{id}         # Delete concept

# Evaluations
POST   /api/v1/concepts/{id}/evaluate     # Run RAG evaluation (~3-5s)
GET    /api/v1/concepts/{id}/evaluation   # Get cached evaluation

# Reports (PDF + vector store CRUD)
POST   /api/v1/reports               # Upload a PDF report and index chunks
GET    /api/v1/reports               # List reports (paginated)
GET    /api/v1/reports/index         # Read/search indexed reports from vector metadata/content
GET    /api/v1/reports/{id}          # Get full report details/content
PUT    /api/v1/reports/{id}          # Update report metadata/content
DELETE /api/v1/reports/{id}          # Delete report + indexed vectors

# Health & Discovery
GET    /api/v1/health                # System status
GET    /api/v1/mcp                   # MCP tool discovery
```

**Full Documentation**: [API_DOCUMENTATION.pdf](docs/API_DOCUMENTATION.pdf) (includes examples, error codes, authentication)  
**Interactive Docs**: http://localhost:8001/docs

### Authentication

All API endpoints (except `/auth/register` and `/auth/login`) require a JWT Bearer token.

```bash
# 1. Register a user
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword"}'

# 2. Login and capture the token
TOKEN=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 3. Use the token in subsequent requests
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/api/v1/concepts
```

---

## Development

### Run Tests

```bash
# All tests (55 total)
uv run pytest tests/ -v

# Specific suites
uv run pytest tests/test_api_errors.py -v      # API error handling (16)
uv run pytest tests/test_database_errors.py -v # DB transactions (13)
uv run pytest tests/test_e2e.py -v             # End-to-end workflows (8)
uv run pytest tests/test_concepts.py -v        # CRUD (13)
uv run pytest tests/test_reports.py -v         # Report CRUD + vector sync (5)
```

See [TESTING.md](TESTING.md) for comprehensive test documentation.

### Database Management

```bash
# Reset database (deletes all data)
rm aeroinsight.db
uv run python -c "from app.core.database import engine, Base; Base.metadata.create_all(engine)"

# Reset vector store (requires re-ingestion)
rm -rf chroma_db/
uv run python scripts/ingest_documents.py
```

### API Testing

```bash
# Health check
curl http://localhost:8001/api/v1/health

# Create concept
curl -X POST http://localhost:8001/api/v1/concepts \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","description":"This is a test description for API validation","author":"Tester"}'

# Evaluate concept (replace {id})
curl -X POST http://localhost:8001/api/v1/concepts/{id}/evaluate

# Upload report (PDF)
curl -X POST http://localhost:8001/api/v1/reports \
  -F "file=@./sample_report.pdf" \
  -F "title=Wind Tunnel Post-Run" \
  -F "author=Aero Team" \
  -F "tags=wind-tunnel,validation"

# Read report index from vector store (metadata + chunk text search)
curl "http://localhost:8001/api/v1/reports/index?query=wind-tunnel"
```

### Generate API PDF Docs

```bash
uv sync --group docs
uv run python scripts/generate_api_docs_pdf.py
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `uvicorn: command not found` | Run with uv-managed env: `uv run uvicorn app.main:app --reload --port 8001` (or run `uv shell` first) |
| `OpenAI API key not found` | Check `.env` file exists with valid key |
| `ChromaDB collection not found` | Run `uv run python scripts/ingest_documents.py` |
| `Port 8001 already in use` | Kill process or use different port: `--port 8002` |
| `Only PDF files are supported` | Upload `.pdf` files only for `/api/v1/reports` |
| `npm: command not found` | Install Node.js 20+ |
| API calls returning CORS errors | Check Vite proxy config in `frontend/vite.config.js` |

---

## Additional Resources

- **Architecture Details**: See [ARCHITECTURE.md](ARCHITECTURE.md) for RAG pipeline, database schema, and design decisions
- **Testing Guide**: See [TESTING.md](TESTING.md) for test suites, error handling, and CI/CD setup
- **API Documentation**: [PDF](docs/API_DOCUMENTATION.pdf) | [Interactive Swagger UI](http://localhost:8001/docs) | [Markdown](docs/API_DOCUMENTATION.md)
- **OpenAI API Keys**: https://platform.openai.com/api-keys

### Technology Docs

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [ChromaDB](https://docs.trychroma.com/)
- [SentenceTransformers](https://sbert.net/)
- [Tailwind CSS](https://tailwindcss.com/docs)

---

## License

This project is provided as-is for educational and research purposes.

**arXiv Papers**: Publicly available under [arXiv's terms of use](https://arxiv.org/help/license)  
**OpenAI API**: Subject to [OpenAI's terms of service](https://openai.com/policies/terms-of-use)

---

*Last Updated: March 2026*
