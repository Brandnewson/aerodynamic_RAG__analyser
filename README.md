# AeroInsight RAG Analyser

A full-stack application for evaluating novel aerodynamic concepts using Retrieval-Augmented Generation (RAG) with arXiv research papers.

![Architecture](docs/architecture-overview.png)

## 🎯 Project Overview

AeroInsight allows researchers and engineers to submit aerodynamic concepts and receive AI-powered evaluations backed by real research papers. The system:

1. **Ingests** 248 arXiv papers (31,652 chunks) into a vector database
2. **Retrieves** semantically similar research when a concept is submitted
3. **Generates** structured evaluations using GPT-4o with citations
4. **Visualizes** results through a fighter jet cockpit-inspired UI

---

## 🏗️ Architecture

### High-Level Overview

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  React Frontend │─────▶│  FastAPI Backend│─────▶│  ChromaDB       │
│  (Port 3000)    │      │  (Port 8001)    │      │  Vector Store   │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │  OpenAI GPT-4o  │
                         │  LLM Evaluation │
                         └─────────────────┘
```

### Technology Stack

#### Backend
- **FastAPI** 0.133.1 - REST API framework
- **SQLite** - Concept persistence with SQLAlchemy ORM
- **ChromaDB** 1.5.1 - Vector database for 31,652 paper chunks
- **SentenceTransformers** 5.2.3 - Local embeddings (all-MiniLM-L6-v2)
- **OpenAI SDK** 2.24.0 - GPT-4o structured JSON evaluation (upgraded reasoning model)
- **Python** 3.12.12 - Runtime with UV package manager

#### Frontend
- **React** 18.3.1 - Component library
- **Vite** 5.1.4 - Build tool and dev server
- **Tailwind CSS** 3.4.1 - Utility-first styling with custom cockpit theme
- **Framer Motion** 11.0.8 - Animation library
- **React Router** 6.22.0 - Client-side routing
- **Lucide React** 0.344.0 - Icon library

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+** with `uv` package manager
- **Node.js 20+** (installed via nvm recommended)
- **OpenAI API Key** ([get one here](https://platform.openai.com/api-keys))
- **Git** for version control

### 1️⃣ Clone & Setup Environment

```bash
# Clone repository
git clone <repository-url>
cd aerodynamic_RAG__analyser

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# Install Python dependencies
uv pip install -r requirements.txt
```

### 2️⃣ Configure Environment Variables

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-api-key-here

# Database Configuration
DATABASE_URL=sqlite:///./aeroinsight.db

# ChromaDB Configuration
CHROMA_PERSIST_DIR=./chroma_storage
CHROMA_COLLECTION_NAME=arxiv_aerodynamics
```

### 3️⃣ Initialize Database

```bash
# Run ingestion pipeline (one-time setup)
python scripts/ingest_data.py

# Expected output:
# Processed 248 papers
# Created 31,652 chunks
# ChromaDB collection ready
```

### 4️⃣ Start Backend Server

```bash
# Activate venv if not already active
.venv\Scripts\Activate.ps1

# Start FastAPI server
python -m uvicorn app.main:app --reload --port 8001

# Server running at http://localhost:8001
# API docs at http://localhost:8001/docs
```

### 5️⃣ Start Frontend Dev Server

```bash
# In a new terminal window
cd frontend

# Install dependencies (first time only)
npm install

# Start Vite dev server
npm run dev

# Frontend running at http://localhost:3000
```

### 6️⃣ Access Application

Open your browser and navigate to:
- **Frontend UI**: http://localhost:3000
- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/api/v1/health

---

## 📖 Usage Guide

### Creating a New Concept

1. Navigate to **Mission Control** (homepage)
2. Click **"+ New Concept"** button
3. Fill in the form:
   - **Title**: Short descriptive name (min 3 characters)
   - **Description**: Detailed explanation (min 20 characters)
   - **Author**: Your name
   - **Tags**: Comma-separated keywords (e.g., `aerodynamics, computational, experimental`)
4. Click **"Create Concept"**
5. Concept appears in the list with status `SUBMITTED`

### Evaluating a Concept

1. Find your concept in the concepts list
2. Click the **"Evaluate"** button (amber color)
3. Wait for RAG pipeline to complete (~5-10 seconds)
4. Scroll to **"Evaluation Results"** section
5. Review:
   - **Novelty Score** (0.0 - 1.0): How original the concept is
   - **Confidence Score** (0.0 - 1.0): LLM's certainty in evaluation
   - **Mechanisms**: List of aerodynamic principles involved
   - **Trade-offs**: Engineering compromises identified
   - **Regulatory Flags**: Safety/compliance concerns
   - **Retrieved Context**: 5 most relevant research papers with citations

### Managing Concepts

- **Edit**: Click pencil icon, modify fields, save changes
- **Delete**: Click trash icon, confirm deletion
- **Filter**: Use status dropdown to filter by `SUBMITTED` or `ANALYSED`
- **Search**: Use search bar to find concepts by title/description
- **View Results**: For analyzed concepts, click "View Results" to see cached evaluations

### Understanding Evaluation Results

**Novelty Score Interpretation:**
- `0.0 - 0.3`: Well-established concept with extensive prior art
- `0.4 - 0.6`: Incremental improvement on existing approaches
- `0.7 - 0.9`: Moderately novel with some unique aspects
- `0.9 - 1.0`: Highly original concept with limited precedent

**Confidence Score Interpretation:**
- `0.0 - 0.5`: Low confidence - more research needed
- `0.6 - 0.8`: Moderate confidence - evaluation is reasonable
- `0.9 - 1.0`: High confidence - strong backing from literature

**Retrieved Context:**
Each citation card shows:
- **Similarity %**: How relevant this paper is to your concept
- **Title & Authors**: Full paper metadata
- **arXiv ID**: Link to original paper on arXiv.org
- **Excerpt**: Key passage related to your concept

---

## 🗂️ Project Structure

```
aerodynamic_RAG__analyser/
├── app/                          # Backend FastAPI application
│   ├── api/                      # API route handlers
│   │   ├── concepts.py           # CRUD endpoints for concepts
│   │   ├── evaluations.py        # RAG evaluation endpoint
│   │   └── health.py             # Health check endpoint
│   ├── core/                     # Core configurations
│   │   ├── config.py             # Environment variable loading
│   │   └── database.py           # SQLAlchemy database setup
│   ├── domain/                   # Domain models
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   └── schemas.py            # Pydantic request/response schemas
│   ├── services/                 # Business logic layer
│   │   └── rag_service.py        # RAG pipeline implementation
│   └── main.py                   # FastAPI application entry point
│
├── frontend/                     # React frontend application
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── layout/           # Layout components
│   │   │   │   ├── Layout.jsx    # Main layout wrapper
│   │   │   │   └── Sidebar.jsx   # Navigation sidebar
│   │   │   ├── concepts/         # Concept-related components
│   │   │   │   ├── ConceptCard.jsx    # Concept display card
│   │   │   │   └── ConceptForm.jsx    # Create/edit modal form
│   │   │   └── evaluations/      # Evaluation-related components
│   │   │       ├── CitationCard.jsx        # Single citation display
│   │   │       ├── RetrievedContext.jsx    # Citation grid wrapper
│   │   │       └── EvaluationResult.jsx    # Full evaluation display
│   │   ├── pages/                # Page components
│   │   │   ├── Dashboard.jsx     # Main mission control page
│   │   │   ├── Documentation.jsx # API documentation
│   │   │   ├── HowItWorks.jsx    # Pipeline explanation
│   │   │   └── HealthCheck.jsx   # System status monitor
│   │   ├── services/             # API service layer
│   │   │   └── api.js            # HTTP request abstraction
│   │   ├── App.jsx               # Router configuration
│   │   ├── main.jsx              # React entry point
│   │   └── index.css             # Global Tailwind styles
│   ├── index.html                # HTML entry point
│   ├── vite.config.js            # Vite configuration
│   ├── tailwind.config.js        # Tailwind + cockpit theme
│   ├── postcss.config.js         # PostCSS configuration
│   └── package.json              # NPM dependencies
│
├── scripts/                      # Utility scripts
│   ├── ingest_data.py            # Initial data ingestion
│   └── test_evaluation.py        # End-to-end test script
│
├── tests/                        # Automated tests
│   ├── test_api.py               # API endpoint tests
│   └── test_rag_service.py       # RAG pipeline tests
│
├── chroma_storage/               # ChromaDB persistence (gitignored)
├── .venv/                        # Python virtual environment (gitignored)
├── aeroinsight.db                # SQLite database (gitignored)
├── .env                          # Environment variables (gitignored)
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## 🔬 RAG Pipeline Deep Dive

### Step-by-Step Evaluation Flow

```
User Submits Concept
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ 1. TEXT EMBEDDING                                             │
│    - Convert concept description to 384-dim vector           │
│    - Model: all-MiniLM-L6-v2 (SentenceTransformers)         │
│    - Same model used during ingestion                        │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ 2. SEMANTIC RETRIEVAL                                         │
│    - Query ChromaDB with embedding vector                    │
│    - Retrieve top 5 most similar chunks                      │
│    - Cosine similarity metric                                │
│    - Returns: chunk text + metadata (arXiv ID, authors)      │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ 3. PROMPT CONSTRUCTION                                        │
│    - Build system prompt with JSON schema definition         │
│    - Build user prompt with:                                 │
│      • Concept title + description                           │
│      • Retrieved chunks with full citations                  │
│      • arXiv metadata (title, authors, publish date)         │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ 4. LLM EVALUATION                                             │
│    - Send prompt to OpenAI GPT-4o                            │
│    - Request structured JSON response                        │
│    - Schema enforced via response_format parameter           │
│    - Returns: novelty, confidence, mechanisms, tradeoffs     │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ 5. RESPONSE PARSING & PERSISTENCE                            │
│    - Parse JSON response from GPT-4o                         │
│    - Clamp novelty/confidence to [0.0, 1.0]                 │
│    - Convert empty strings to None                           │
│    - Save evaluation to SQLite                               │
│    - Build citation objects from metadata                    │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
    Return EvaluationResponse
    with retrieved_context
```

### RAG Service Code Structure

```python
# app/services/rag_service.py

class RAGService:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.PersistentClient(path="./chroma_storage")
        self.collection = self.chroma_client.get_collection("arxiv_aerodynamics")
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def evaluate_concept(self, db: Session, concept: Concept) -> tuple[ConceptEvaluation, list[RetrievedChunk]]:
        """Main evaluation pipeline - returns tuple for API response building"""
        
        # Step 1: Text Embedding
        embedding = self._embed_text(concept.description)
        
        # Step 2: Semantic Retrieval
        results = self.collection.query(
            query_embeddings=[embedding.tolist()],
            n_results=5,
            include=["documents", "metadatas", "distances"]
        )
        
        # Step 3: Prompt Construction
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(concept, results)
        
        # Step 4: LLM Evaluation
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # Step 5: Response Parsing & Persistence
        evaluation = self._build_evaluation(concept, response)
        db.add(evaluation)
        db.commit()
        
        retrieved_chunks = self._build_retrieved_chunks(results)
        return evaluation, retrieved_chunks
```

### Key Design Decisions

**Why SentenceTransformers instead of OpenAI embeddings?**
- **Cost**: Local embeddings are free after initial download
- **Speed**: No API latency for embedding generation
- **Privacy**: Sensitive concepts never leave your infrastructure
- **Consistency**: Same model for ingestion and retrieval guarantees

**Why ChromaDB instead of Pinecone/Weaviate?**
- **Simplicity**: No external services required
- **Persistence**: Built-in disk storage with minimal config
- **Performance**: Fast enough for 31k chunks on local hardware
- **Development**: Easy to reset/modify during experimentation

**Why GPT-4o instead of GPT-4o-mini?**
- **Reasoning**: Superior logical analysis of complex aerodynamic concepts
- **JSON Adherence**: More reliable structured output generation
- **Context**: Handles longer retrieved context without degradation
- **Citation Quality**: Better at connecting concepts to research literature
- **Cost vs Quality**: Full model provides significantly better evaluation quality

---

## 🎨 Frontend Design System

### Cockpit Theme Philosophy

The UI is inspired by fighter jet cockpits (specifically Saab 9000s design principles):
- **Functional First**: Every element serves a purpose, no decorative fluff
- **High Contrast**: Critical information stands out immediately
- **Consistent Patterns**: Repeated UI patterns reduce cognitive load
- **Efficient Workflow**: Minimal clicks to accomplish tasks

### Color Palette

```css
/* Cockpit Theme Variables */
--cockpit-bg: #0a0e14;          /* Deep space background */
--cockpit-primary: #ff9500;     /* Amber HUD indicators */
--cockpit-secondary: #00d9ff;   /* Cyan displays */
--cockpit-danger: #ff4757;      /* Red alerts */
--cockpit-success: #2ecc71;     /* Green status */
--cockpit-text: #e5e7eb;        /* Light gray text */
--cockpit-muted: #6b7280;       /* Muted secondary text */
```

### Typography

- **Display/Headers**: Rajdhani (geometric, technical feel)
- **Body Text**: System sans-serif stack for readability
- **Code/Metrics**: JetBrains Mono (monospace for data)

**Avoided**: Inter, Roboto, Poppins (generic "AI product" aesthetic)

### Component Patterns

**Panels** - Containers with subtle borders and dark backgrounds
```jsx
<div className="panel">
  {/* Content */}
</div>
```

**Buttons** - Color-coded by action type
```jsx
<button className="btn-primary">Evaluate</button>    {/* Amber */}
<button className="btn-secondary">Edit</button>      {/* Cyan */}
<button className="btn-danger">Delete</button>       {/* Red */}
```

**Badges** - Status indicators with context colors
```jsx
<span className="badge badge-cyan">SUBMITTED</span>
<span className="badge badge-green">ANALYSED</span>
```

**Metrics** - Large numbers with labels
```jsx
<div className="metric">
  <div className="metric-value">0.85</div>
  <div className="metric-label">Novelty Score</div>
</div>
```

### Animation Guidelines

All animations use Framer Motion with consistent timing:
- **Entry Animations**: 0.3s slide-in + fade-in
- **Staggered Lists**: 0.1s delay between items
- **Hover Effects**: 0.2s scale + glow
- **Loading States**: 1.5s pulse animation

```jsx
import { motion } from 'framer-motion';

<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.3 }}
>
  {/* Content */}
</motion.div>
```

---

## 🗄️ Database Schema

### Concepts Table

```sql
CREATE TABLE concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    author VARCHAR(100),
    tags TEXT,                          -- JSON array stored as string
    status VARCHAR(20) DEFAULT 'SUBMITTED',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Concept Evaluations Table

```sql
CREATE TABLE concept_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_id INTEGER NOT NULL UNIQUE,  -- One-to-one relationship
    novelty_score REAL NOT NULL,
    confidence_score REAL NOT NULL,
    mechanisms TEXT,                     -- JSON array
    tradeoffs TEXT,                      -- JSON array
    regulatory TEXT,                     -- JSON array
    summary TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (concept_id) REFERENCES concepts(id) ON DELETE CASCADE
);
```

### Relationships

- **One Concept → One Evaluation** (one-to-one via `concept_id` UNIQUE constraint)
- **Cascade Delete**: Deleting a concept deletes its evaluation automatically
- **JSON Serialization**: Arrays stored as JSON strings (SQLite limitation)

### Example Data

```json
// Concept
{
  "id": 1,
  "title": "Ground effect diffuser with active flow control",
  "description": "A wing diffuser that uses boundary layer suction...",
  "author": "John Doe",
  "tags": ["aerodynamics", "ground-effect", "active-control"],
  "status": "ANALYSED",
  "created_at": "2026-02-28T10:30:00Z"
}

// Evaluation
{
  "id": 1,
  "concept_id": 1,
  "novelty_score": 0.80,
  "confidence_score": 0.90,
  "mechanisms": [
    "Boundary layer suction reduces separation",
    "Ground effect increases downforce"
  ],
  "tradeoffs": [
    "Increased complexity vs improved performance",
    "Power consumption vs drag reduction"
  ],
  "regulatory": [
    "FIA technical regulations may restrict active aero"
  ],
  "summary": "Moderately novel concept combining established principles..."
}
```

---

## 🛠️ Development Workflow

### Running Tests

```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run all tests
pytest

# Run specific test file
pytest tests/test_rag_service.py

# Run with coverage report
pytest --cov=app tests/

# Run with verbose output
pytest -v
```

### Database Management

```bash
# Reset database (caution: deletes all data)
rm aeroinsight.db
python -c "from app.core.database import engine, Base; Base.metadata.create_all(engine)"

# View database schema
sqlite3 aeroinsight.db ".schema"

# Query concepts
sqlite3 aeroinsight.db "SELECT * FROM concepts;"

# Backup database
cp aeroinsight.db aeroinsight_backup_$(date +%Y%m%d).db
```

### ChromaDB Management

```bash
# Reset vector database (caution: requires re-ingestion)
rm -rf chroma_storage/
python scripts/ingest_data.py

# Check collection stats
python -c "import chromadb; client = chromadb.PersistentClient(path='./chroma_storage'); print(client.get_collection('arxiv_aerodynamics').count())"

# Query vector database directly
python
>>> import chromadb
>>> client = chromadb.PersistentClient(path='./chroma_storage')
>>> collection = client.get_collection('arxiv_aerodynamics')
>>> results = collection.peek(limit=5)  # View first 5 chunks
```

### Frontend Development

```bash
# Install new dependency
cd frontend
npm install <package-name>

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Format code (if configured)
npm run format
```

### API Testing

```bash
# Health check
curl http://localhost:8001/api/v1/health

# List concepts
curl http://localhost:8001/api/v1/concepts

# Create concept
curl -X POST http://localhost:8001/api/v1/concepts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Concept",
    "description": "A test aerodynamic concept for validation",
    "author": "Test User",
    "tags": ["test", "validation"]
  }'

# Evaluate concept (replace {id} with concept ID)
curl -X POST http://localhost:8001/api/v1/concepts/{id}/evaluate

# Get evaluation (retrieve stored result)
curl http://localhost:8001/api/v1/concepts/{id}/evaluation
```

### Code Style Guidelines

**Python (Backend)**
- Follow PEP 8 style guide
- Use type hints for function signatures
- Docstrings for public methods (Google style)
- Max line length: 100 characters
- Use `black` for auto-formatting

**JavaScript/React (Frontend)**
- Use ES6+ syntax (arrow functions, destructuring)
- Functional components with hooks (no class components)
- PropTypes or TypeScript for type safety (optional)
- 2-space indentation
- Use Prettier for auto-formatting

---

## 🐛 Troubleshooting

### Backend Issues

**Problem**: `uvicorn: command not found`
```bash
# Solution: Activate virtual environment
.venv\Scripts\Activate.ps1

# Verify activation (should show venv path)
which python
```

**Problem**: `OpenAI API key not found`
```bash
# Solution: Check .env file exists and has correct key
cat .env | grep OPENAI_API_KEY

# Restart server after adding key
```

**Problem**: `ChromaDB collection not found`
```bash
# Solution: Run ingestion script
python scripts/ingest_data.py

# Check collection was created
ls chroma_storage/
```

**Problem**: `Port 8001 already in use`
```bash
# Solution: Kill existing process
# Windows:
netstat -ano | findstr :8001
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8001 | xargs kill -9

# Or use different port:
python -m uvicorn app.main:app --reload --port 8002
```

### Frontend Issues

**Problem**: `npm: command not found`
```bash
# Solution: Install Node.js via nvm
nvm install 22
nvm use 22
node --version  # Should show v22.x.x
```

**Problem**: `Failed to resolve import`
```bash
# Solution: Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Problem**: `Port 3000 already in use`
```bash
# Solution: Vite will automatically try 3001, 3002, etc.
# Or specify port:
npm run dev -- --port 3005
```

**Problem**: `API calls returning CORS errors`
```bash
# Solution: Check Vite proxy config is correct
cat frontend/vite.config.js

# Should have:
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8001',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '')
    }
  }
}

# In production, configure FastAPI CORS:
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Database Issues

**Problem**: `Database is locked`
```bash
# Solution: Close all connections and restart
# Check for open connections:
lsof aeroinsight.db  # Linux/Mac
# Windows: Use Process Explorer

# Force close and restart server
```

**Problem**: `Foreign key constraint failed`
```bash
# Solution: SQLite foreign keys may not be enabled
# Add to database.py:
engine = create_engine(
    "sqlite:///./aeroinsight.db",
    connect_args={"check_same_thread": False},
    echo=True
)

# Enable foreign keys in session:
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

### Common Mistakes

**Mistake**: Creating concepts without descriptions
```
Error: description must be at least 20 characters
Solution: Provide detailed concept descriptions
```

**Mistake**: Evaluating same concept multiple times
```
Result: Overwrites previous evaluation (one-to-one relationship)
Solution: This is expected behavior - concepts have one evaluation
```

**Mistake**: Forgetting to restart server after .env changes
```
Symptom: API key errors persist
Solution: Always restart uvicorn after modifying .env
```

---

## 📊 Performance Considerations

### Backend Performance

**Ingestion Speed** (248 papers):
- Parsing PDFs: ~2-3 minutes
- Chunking text: ~30 seconds
- Generating embeddings: ~5-8 minutes (CPU)
- ChromaDB insertion: ~1 minute
- **Total**: ~10-15 minutes initial setup

**Evaluation Speed** (per concept):
- Embedding generation: ~50ms (local)
- Chromo API call: ~2-4 seconds
- Database persistence: ~50ms
- **Total**: ~3-5 seconds per evaluation

**Note**: Evaluation results are cached in SQLite. Re-evaluating an existing concept returns a 409 Conflict error - delete and recreate the concept to re-run evaluation.
- **Total**: ~4-6 seconds per evaluation

### Frontend Performance

**Bundle Size** (production build):
- Vendor chunks: ~200KB gzipped
- App code: ~50KB gzipped
- CSS: ~10KB gzipped
- **Total**: ~260KB gzipped

**Lighthouse Scores** (typical):
- Performance: 95+
- Accessibility: 100
- Best Practices: 100
- SEO: 90+

### Optimization Tips

**Backend**:
- Cache embeddings for frequently evaluated concepts
- Use GPU for SentenceTransformers (5-10x faster)
- Batch multiple evaluations with asyncio
- Consider GPT-3.5-turbo for faster/cheaper evaluations

**Frontend**:
- Lazy load evaluation results (only fetch when needed)
- Implement virtual scrolling for large concept lists
- Use SWR or React Query for caching API responses
- Code split routes for faster initial load

---

## 🚢 Deployment

### Production Checklist

Before deploying to production:

- [ ] Change `DEBUG = False` in FastAPI settings
- [ ] Set secure `SECRET_KEY` in environment variables
- [ ] Configure production database (PostgreSQL recommended)
- [ ] Set up Redis for caching (optional but recommended)
- [ ] Configure CORS for production frontend domain
- [ ] Set up HTTPS (SSL certificates)
- [ ] Configure rate limiting on API endpoints
- [ ] Set up monitoring (Sentry, DataDog, etc.)
- [ ] Configure backup strategy for database
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Review and limit OpenAI API spending cap

### Docker Deployment (Optional)

```dockerfile
# Backend Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

```dockerfile
# Frontend Dockerfile
FROM node:22-alpine as build

WORKDIR /app

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8001:8001"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=sqlite:///./aeroinsight.db
    volumes:
      - ./chroma_storage:/app/chroma_storage
      - ./aeroinsight.db:/app/aeroinsight.db

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
```

---

## 🤝 Contributing

### Development Setup for Contributors

1. Fork the repository
2. Clone your fork: `git clone <your-fork-url>`
3. Create feature branch: `git checkout -b feature/amazing-feature`
4. Make changes and test thoroughly
5. Commit with clear messages: `git commit -m "Add amazing feature"`
6. Push to your fork: `git push origin feature/amazing-feature`
7. Open Pull Request with detailed description

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] All tests pass (`pytest`)
- [ ] New features have tests
- [ ] Documentation updated (README, docstrings)
- [ ] No console.log or debug statements
- [ ] Environment variables documented
- [ ] Breaking changes clearly noted

---

## 📝 License

This project is provided as-is for educational and research purposes. 

**arXiv Papers**: All referenced papers are publicly available under [arXiv's terms of use](https://arxiv.org/help/license).

**OpenAI API**: Usage subject to [OpenAI's terms of service](https://openai.com/policies/terms-of-use).

---

## 🙏 Acknowledgments

- **arXiv.org**: For providing open access to research papers
- **OpenAI**: For GPT-4o API access
- **ChromaDB**: For easy-to-use vector database
- **SentenceTransformers**: For high-quality embedding models
- **Tailwind CSS**: For utility-first styling framework
- **Framer Motion**: For smooth animations

---

## 📞 Support

For questions, issues, or feature requests:

1. **Check Documentation**: Review this README thoroughly
2. **Search Issues**: Look for similar problems in GitHub Issues
3. **Create Issue**: Open a new issue with detailed description
4. **Community**: Join discussions in GitHub Discussions

---

## 🗺️ Roadmap

Future enhancements planned:

- [ ] **User Authentication**: Multi-user support with JWT tokens
- [ ] **Concept Versioning**: Track changes to concepts over time
- [ ] **Comparison View**: Side-by-side concept comparison
- [ ] **Export Reports**: PDF/Word export of evaluations
- [ ] **Advanced Filters**: Filter by novelty score, date range, author
- [ ] **Batch Evaluation**: Evaluate multiple concepts at once
- [ ] **Custom Models**: Support for local LLMs (Llama, Mistral)
- [ ] **Real-time Collaboration**: WebSocket support for team use
- [ ] **Mobile App**: React Native companion app
- [ ] **API Versioning**: v2 API with GraphQL option

---

## 📚 Additional Resources

### Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [SentenceTransformers Documentation](https://www.sbert.net/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

### Related Papers

- [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401)
- [Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks](https://arxiv.org/abs/1908.10084)
- [Dense Passage Retrieval for Open-Domain Question Answering](https://arxiv.org/abs/2004.04906)

---

**Built with ❤️ for aerospace innovation research**

*Last Updated: February 28, 2026*