# AeroInsight RAG Analyser

AI-powered evaluation of aerodynamic concepts using Retrieval-Augmented Generation (RAG) with arXiv research papers.

## What It Does

Submit aerodynamic concepts → Get AI evaluations backed by real research papers

1. **Vector Search**: Queries 31,652 chunks from 248 arXiv papers
2. **LLM Evaluation**: GPT-4o analyzes novelty, mechanisms, and tradeoffs
3. **Structured Output**: Novelty scores, confidence, regulatory flags, citations

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
python -m venv .venv

# Windows:
.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

uv pip install -r requirements.txt

# 2. Configure environment
# Create .env file with:
OPENAI_API_KEY=sk-proj-your-key-here
DATABASE_URL=sqlite:///./database.db
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION_NAME=arxiv_aerodynamics

# 3. Initialize database
python scripts/ingest_documents.py  # One-time: ingests 248 papers (~10-15 min)

# 4. Start backend
python -m uvicorn app.main:app --reload --port 8001
# Running at http://localhost:8001

# 5. Start frontend (new terminal)
cd frontend
npm install
npm run dev
# Running at http://localhost:3000
```

**Verify**: Open http://localhost:3000 and create a concept.

---

## API Overview

### REST Endpoints

```bash
# Concepts
GET    /api/v1/concepts              # List concepts (paginated, filterable)
GET    /api/v1/concepts/{id}         # Get single concept
POST   /api/v1/concepts              # Create concept
PATCH  /api/v1/concepts/{id}         # Update concept
DELETE /api/v1/concepts/{id}         # Delete concept

# Evaluations
POST   /api/v1/concepts/{id}/evaluate     # Run RAG evaluation (~3-5s)
GET    /api/v1/concepts/{id}/evaluation   # Get cached evaluation

# Health & Discovery
GET    /api/v1/health                # System status
GET    /api/v1/mcp                   # MCP tool discovery
```

**Interactive Docs**: http://localhost:8001/docs

---

## Development

### Run Tests

```bash
# All tests (49 total - 100% passing)
uv run pytest tests/ -v

# Specific suites
uv run pytest tests/test_api_errors.py -v      # API error handling (16)
uv run pytest tests/test_database_errors.py -v # DB transactions (13)
uv run pytest tests/test_e2e.py -v             # End-to-end (7)
uv run pytest tests/test_concepts.py -v        # CRUD (13)
```

See [TESTING.md](TESTING.md) for comprehensive test documentation.

### Database Management

```bash
# Reset database (deletes all data)
rm aeroinsight.db
python -c "from app.core.database import engine, Base; Base.metadata.create_all(engine)"

# Reset vector store (requires re-ingestion)
rm -rf chroma_db/
python scripts/ingest_documents.py
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
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `uvicorn: command not found` | Activate venv: `.venv\Scripts\Activate.ps1` |
| `OpenAI API key not found` | Check `.env` file exists with valid key |
| `ChromaDB collection not found` | Run `python scripts/ingest_documents.py` |
| `Port 8001 already in use` | Kill process or use different port: `--port 8002` |
| `npm: command not found` | Install Node.js 20+ |
| API calls returning CORS errors | Check Vite proxy config in `frontend/vite.config.js` |

---

## Additional Resources

- **Architecture Details**: See [ARCHITECTURE.md](ARCHITECTURE.md) for RAG pipeline, database schema, and design decisions
- **Testing Guide**: See [TESTING.md](TESTING.md) for test suites, error handling, and CI/CD setup
- **API Documentation**: http://localhost:8001/docs (interactive Swagger UI)
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
